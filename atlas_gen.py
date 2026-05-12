#!/usr/bin/env python3

import sys
import argparse
from PIL import Image, ImageFont, ImageDraw
import numpy as np
import json
from typing import Tuple, IO
from pathlib import Path
import lzma

from rect_packer import MaxRectPacker

# 格式：{(字体文件路径: Path, 字体号(ttc文件专用，否则默认0即可): int, size值: int): ImageFont.FreeTypeFont}
# FontPool = dict()


class Char():
    def __init__(self):
        self.code = 65535
        self.char = ""
        self.pageID = -1  # 所属Page
        (self.u1, self.u2, self.v1, self.v2) = (0, 0, 0, 0)
        self.pixPos = (0, 0)  # 在大图中的左上角点，像素值，(x, y)

        self.img: Image.Image = None
        self.imgData_P: np.ndarray = None

    def gen_img(self, code: int, fontPath: Path, size: int, border: int = 2, superSample: int = 1, ttcIndex: int = 0):
        """
        生成字图。
        需要传入字符的Unicode号、目标字号大小(PIL)、字图底边距
        超采样倍数若设为>1的数则通过超采样方式取得字图，即先生成大的再缩小回来
        """
        self.code = code
        self.char = chr(self.code)

        font = ImageFont.truetype(fontPath, size * superSample, ttcIndex)

        (left, top, right, bottom) = font.getbbox(self.char)
        w1 = (right - left)
        h1 = (bottom - top) + border * superSample

        img = Image.new("RGB", (w1, h1), (0, 0, 0))

        draw = ImageDraw.Draw(img, "RGB")
        draw.text((0, 0), self.char, fill=(255, 255, 255), font=font)

        # print(w1, h1, w1 / superSample, h1 / superSample)
        self.img = (img if (superSample == 1) else img.resize(
            (np.ceil(w1 / superSample).astype(int), np.ceil(h1 / superSample).astype(int))))

    def set_pixPos(self, x: int, y: int):
        self.pixPos = (x, y)

    def calc_uv(self, U: int, V: int):
        """
        计算uv值，U、V分别为大图的横、竖方向长度(像素)
        """
        (dx, dy) = self.img.size
        (x1, y1) = self.pixPos
        x2 = x1 + dx
        y2 = y1 + dy

        (self.u1, self.v1) = (x1 / U, y1 / V)
        (self.u2, self.v2) = (x2 / U, y2 / V)

    def get_dict(self) -> dict:
        return {"code": self.code,
                "page": self.pageID,
                "u1": self.u1,
                "u2": self.u2,
                "v1": self.v1,
                "v2": self.v2}


class Page():
    def __init__(self):
        self.pageID = -1
        self.img: Image.Image = None  # 大图

        self.imgData_P: np.ndarray = None  # 二维数组
        self.imgData_CLUT4: np.ndarray = None  # 一维数组

        self.charList: [Char] = []

    def import_chars(self, charList: [Char]):
        self.charList = charList
        self.charList.sort(key=lambda x: x.code)

    def init_canvas(self, canvasSize: Tuple[int, int]):
        self.img = Image.new("RGB", canvasSize, (0, 0, 0))

    def set_pageID(self, pageID: int):
        self.pageID = pageID

    def get_info(self) -> dict:
        (w, h) = self.img.size
        return {"pixWidth": w,
                "pixHeight": h,
                "pageSize": len(self.imgData_CLUT4),
                "pageFile": "page{0:n}.CLUT4".format(self.pageID)
                }

    def build_data_CLUT4(self):
        """
        构建4bit图数据
        反过来看，读取CLUT时，[后4b, 前4b]
        """
        imgData_CLUT4 = []
        data_p = self.imgData_P.reshape(-1)

        p = 0
        while (p < len(data_p)):
            ____dddd = data_p[p]
            dddd____ = data_p[p + 1]

            imgData_CLUT4.append((____dddd & 0b00001111) |
                                 ((dddd____ << 4) & 0b11110000))

            p += 2

        self.imgData_CLUT4 = np.array(imgData_CLUT4, dtype=np.uint8)

    def build_data_P(self):
        """
        根据PIL绘制的图像数据，推导获得索引数据
        PIL画黑白图，再转换到索引式，也能把颜色控制在16内，但是其颜色号分配规则为：
        [背景黑, 最亮白, ..., 最暗]
        而MSXX FontLib纹理的颜色号分配规则则是：
        [背景黑, 最暗, ..., 最亮白]
        """
        self.imgData_P = np.array(self.img.convert("P").get_flattened_data(),
                                  dtype=np.uint8).reshape(self.img.size)
        # print(np.array(self.img.convert("P").getpalette()))

        # 制作一个PIL索引号到fontlib索引号的映射表，用于转换
        colorIndexRange = sorted(set(int(i)
                                     for i in self.imgData_P.reshape(-1)))[1:]
        # print(colorIndexRange, len(colorIndexRange))
        colorIndexRange_fix = [int(round(i, 0)) for i in np.linspace(
            15, 1, len(colorIndexRange))]
        # colorIndexRange = colorIndexRange[:1] + colorIndexRange_fix
        colorIndexDict = {
            colorIndexRange[i]: colorIndexRange_fix[i] for i in range(len(colorIndexRange))}

        (h, w) = self.imgData_P.shape
        for y in range(h):
            for x in range(w):
                if (self.imgData_P[y, x] != 0):
                    self.imgData_P[
                        y, x] = colorIndexDict[self.imgData_P[y, x]]

    def gen_img(self):
        for c in self.charList:
            self.img.paste(c.img, c.pixPos)

    def save_data(self):
        """
        保存纹理图数据：
        预览用的png图、xz压缩的索引模式图像数据(无调色盘)、CLUT4模式图像数据
        """
        fileName = "page{0:n}".format(self.pageID)

        self.img.save(Path("{0:s}_PIL.png".format(fileName)))

        PDataFile = lzma.open(Path("{0:s}.P.xz".format(
            fileName)), "wb", format=lzma.FORMAT_XZ, preset=9)
        PDataFile.write(self.imgData_P)
        PDataFile.close()

        CLUTFile = open(Path("{0:s}.CLUT4".format(fileName)), "wb")
        self.imgData_CLUT4.tofile(CLUTFile)
        CLUTFile.close()


def generate(projFilePath: Path):
    """
    读取项目设定文件(proj)，生成Makefile.json。
    """
    projFile = open(projFilePath, "rt")
    proj = json.load(projFile)
    projFile.close()

    # 由于目前仍不清楚specialCharTable到底何意，目前照抄处理
    makeFile_dict = dict()
    makeFile_dict["specialCharTable"] = [
        ord(c) for c in proj["specialCharTable"]]

    charSize = proj["charSize"]  # 每个单字大小

    # 按配置生成字图，加入到charList中
    charList = []
    for font in proj["fonts"]:
        _str = []
        if (font.get("charStr", None)):
            _str.append(font["charStr"])
        if (font.get("charFile", None)):
            txtFile = open(Path(font["charFile"]), "rt")
            text = txtFile.read()
            txtFile.close()

            _str.append("".join(set("".join(text.splitlines()))))

        for c in "".join(_str):
            cObj = Char()
            cObj.gen_img(ord(c), Path(
                font["fontFile"]), charSize, font["border"], font["superSample"], font["ttcIndex"])

            charList.append(cObj)

    # 主映射表先都用65535占位，表长为所有字符中unicode码最大值
    makeFile_dict["mainMappingTable"] = [65535 for _ in range(
        max([c.code for c in charList]) + 1)]

    packer = MaxRectPacker(proj["pagePixSize"])  # 打包进大图，安排好纹理页去向
    packer.pack(charList)

    for c in charList:
        (U, V) = proj["pagePixSize"]
        c.calc_uv(U, V)

    # 生成纹理页
    pageList = []
    makeFile_dict["pageInfoTable"] = []
    for i in range(packer.page_count()):
        page = Page()
        page.set_pageID(i)
        page.init_canvas(proj["pagePixSize"])
        page.import_chars([c for c in charList if (c.pageID == i)])

        page.gen_img()
        # page.img.show()
        page.build_data_P()
        page.build_data_CLUT4()
        page.save_data()

        pageList.append(page)

        makeFile_dict["pageInfoTable"].append(page.get_info())

    # 按纹理页顺序排字
    charList2 = []
    for page in pageList:
        charList2 += page.charList

    # 上述顺序作为charInfoTable内顺序，确定主映射表
    makeFile_dict["charInfoTable"] = []
    # print("len(mainMappingTable) = {0:n}".format(
    #    len(makeFile_dict["mainMappingTable"])))
    for i in range(len(charList2)):
        # print(charList2[i].code)
        makeFile_dict["mainMappingTable"][charList2[i].code] = i
        makeFile_dict["charInfoTable"].append(charList2[i].get_dict())

    jsonFilePath = Path("Makefile.json").absolute()
    jsonFile = open(jsonFilePath, "wt")
    json.dump(makeFile_dict, jsonFile, ensure_ascii=False, indent='\t')
    jsonFile.close()
    if (jsonFilePath.exists()):
        print("{0}已生成".format(jsonFilePath))


def main():
    cmdParser = argparse.ArgumentParser(
        description="通过配置文件构建MSXX FontLib备用数据与Makefile.json的工具。")
    cmdParser.add_argument("inFilePath", type=Path, help="传入文件路径")
    args = cmdParser.parse_args()

    generate(args.inFilePath)


if (__name__ == "__main__"):
    sys.exit(main())
