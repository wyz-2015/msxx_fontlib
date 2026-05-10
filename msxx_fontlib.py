#!/usr/bin/env python3

import sys
import numpy as np
import argparse
from PIL import Image
from pathlib import Path
from typing import IO
import json

TestPalette = np.array([[c, c, c] for c in range(0, 256, 16)], dtype=np.uint8)


class MainMappingTable():
    def __init__(self, file: IO[bytes]):
        self.data = np.zeros(0, dtype=np.ushort)
        self.file = file

        self.table = []

    def __str__(self):
        return "MainMappingTable[{0:n}]=\n{1}".format(len(self.data), self.data)

    def __expr__(self):
        return self.__str__()

    def read_from_bin(self):
        tableSize = np.fromfile(self.file, np.ushort, 1)[0]
        self.data = np.fromfile(self.file, np.ushort, tableSize)

        self.table = [int(i) for i in self.data]

    def write_to_bin(self):
        np.ushort(len(self.data)).tofile(self.file)
        np.array(self.data, dtype=np.ushort).tofile(self.file)

    def get_dict(self) -> dict:
        return {"mainMappingTable_len": len(self.table), "mainMappingTable": self.table}

    def read_from_dict(self, data: dict):
        self.table = data["mainMappingTable"]


class SpecialCharTable(MainMappingTable):
    def __init__(self, file: IO[bytes]):
        super(SpecialCharTable, self).__init__(file)

    def __str__(self):
        return "SpecialCharTable[{0:n}]=\n{1}".format(len(self.data), self.data)

    def get_dict(self) -> dict:
        return {"specialCharTable_len": len(self.table), "specialCharTable": self.table}

    def read_from_dict(self, data: dict):
        self.table = data["specialCharTable"]


class CharInfoTable():
    CharInfoStruct = np.dtype([
        # ("unknown", np.uint8, (20,))
        ("code", np.uint16),
        ("page", np.uint16),
        ("u1", np.float32),
        ("u2", np.float32),
        ("v1", np.float32),
        ("v2", np.float32)
    ])

    def __init__(self, file: IO[bytes]):
        self.data = np.zeros(0, dtype=self.CharInfoStruct)
        self.file = file

        self.table = []

    def __str__(self):
        return "CharInfoTable[{0:n}]=\n{1}\n包含字符：{2:s}".format(
            len(self.data), self.data,
            "".join([chr(c["code"]) for c in self.data])
        )

    def __expr__(self):
        return self.__str__()

    def read_from_bin(self):
        tableSize = np.fromfile(self.file, np.ushort, 1)[0]
        self.data = np.fromfile(self.file, self.CharInfoStruct, tableSize)

        self.table = [
            {"code": int(i["code"]),
             "char": chr(i["code"]),
             "page": int(i["page"]),
             "u1": float(i["u1"]),
             "u2": float(i["u2"]),
             "v1": float(i["v1"]),
             "v2": float(i["v2"])} for i in self.data
        ]

    def write_to_bin(self):
        np.ushort(len(self.data)).tofile(self.file)
        np.array(self.data, dtype=self.CharInfoStruct).tofile(self.file)

    def get_dict(self) -> dict:
        return {"charInfoTable_len": len(self.table), "charInfoTable": self.table}

    def read_from_dict(self, data: dict):
        self.table = data["charInfoTable"]


class PageTable():
    InfoStruct = np.dtype([
        ("pixWidth", np.uint32),
        ("pixHeight", np.uint32),
        ("pageSize", np.uint32),
        ("address", np.uint32)
    ])

    def __init__(self, file: IO[bytes]):
        self.pageInfoData = np.zeros(0, dtype=self.InfoStruct)
        self.pageData = []
        self.file = file

        self.pageInfoTable = []

    def __str__(self):
        return "PageTableInfo[{0:n}]=\n{1}\nPageTable[{0:n}]=\n{2}".format(
            len(self.pageInfoTable), self.pageInfoData, self.pageData
        )

    def __expr__(self):
        return self.__str__()

    def read_info_from_bin(self):
        tableSize = np.fromfile(self.file, np.uint8, 1)[0]
        self.pageInfoData = np.fromfile(self.file, self.InfoStruct, tableSize)

        self.pageInfoTable = [
            {"pixWidth": int(i["pixWidth"]),
             "pixHeight": int(i["pixHeight"]),
             "pageSize": int(i["pageSize"]),
             "address": int(i["address"])} for i in self.pageInfoData
        ]

    def write_info_to_bin(self):
        np.ushort(len(self.infoData)).tofile(self.file)
        np.array(self.infoData, dtype=self.InfoStruct).tofile(self.file)

    def read_page_from_bin(self):
        for pageInfo in self.pageInfoData:
            pageSize = pageInfo["pageSize"]
            page = np.fromfile(self.file, np.uint8, pageSize)

            self.pageData.append(page)
        # print("pageData[0] = {0}".format(self.pageData[0][:32]))

    def write_page_to_bin(self):
        pass

    def dump_page_texture(self, outDir: Path):
        """
        尝试用一种猜测的调色盘提取纹理
        """
        for i in range(len(self.pageData)):
            data2 = []
            for p2 in self.pageData[i]:
                data2.append(p2 & 0b1111)
                data2.append((p2 >> 4) & 0b1111)

            (w, h) = (int(self.pageInfoData[i]["pixWidth"]), int(
                self.pageInfoData[i]["pixHeight"]))
            img = Image.new("P", (w, h))
            data3 = np.array(data2, dtype=np.uint8)
            # print(len(data3), data3)
            img.putdata(data3)
            img.putpalette(TestPalette, "RGB")
            img.convert("RGBA")
            img.save(outDir / "page{0:n}.png".format(i))
            img.close()

    def get_info_dict(self) -> dict:
        return {"pageInfoTable_len": len(self.pageInfoData), "pageInfoTable": self.pageInfoTable}

    def read_from_dict(self, data: dict):
        self.pageInfoTable = data["pageInfoTable"]


def read(args: argparse.Namespace):
    fontBin = open(args.inFilePath, "rb")

    t1 = MainMappingTable(fontBin)
    t1.read_from_bin()
    print(t1)

    t2 = SpecialCharTable(fontBin)
    t2.read_from_bin()
    print(t2)

    t3 = CharInfoTable(fontBin)
    t3.read_from_bin()
    print(t3)

    t4 = PageTable(fontBin)
    t4.read_info_from_bin()
    t4.read_page_from_bin()
    print(t4)

    print(fontBin.tell())
    fontBin.close()

    if (args.outDir):
        dataDict = dict()
        dataDict.update(t1.get_dict())
        dataDict.update(t2.get_dict())
        dataDict.update(t3.get_dict())
        dataDict.update(t4.get_info_dict())

        outJsonFilePath = args.outDir / "{0}.json".format(args.inFilePath.stem)
        jsonFile = open(outJsonFilePath, "wt")
        json.dump(dataDict, jsonFile, ensure_ascii=False, indent='\t')
        jsonFile.close()

        t4.dump_page_texture(args.outDir)


def main():
    cmdParser = argparse.ArgumentParser(
        description="PSP Metal Slug XX “FONT_LIB.BIN”文件解析与仿制工具")
    modeParser = cmdParser.add_subparsers(dest="mode", help="使用模式")  # ,
    # choices={"read", "write"})

    readParser = modeParser.add_parser("read", help="读取模式")
    readParser.add_argument("inFilePath", type=Path, help="传入fontlib文件路径")
    readParser.add_argument(
        "-d", "--out-dir", help="输出文件目录。若未指定则不另存文件，仅在stdout中输出信息", required=None, type=Path, dest="outDir")

    writeParser = modeParser.add_parser("write", help="制作模式")

    args = cmdParser.parse_args()

    match (args.mode):
        case "read":
            read(args)

        case "write":
            raise ValueError("此功能尚未完成……")

        case _:
            raise ValueError("未知模式字符串{0:s}".format(args.mode))


if (__name__ == "__main__"):
    sys.exit(main())
