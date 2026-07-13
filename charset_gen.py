#!/usr/bin/env python3

import json
import argparse
from pathlib import Path
import sys
from fontTools.ttLib import TTFont, TTCollection


def get_full_set(lineData: dict) -> set:
    """
    从专门的文本数据文件中取得字符全集。
    """
    charSet_full = set()

    for blockSet in lineData:
        for block in blockSet["blockList"]:
            for _str in block["strList"]:
                for c in _str:
                    charSet_full.add(c)

    return charSet_full


def filter_printable(charSet: set[str]) -> dict:
    """
    区别可打印与非可打印字符。
    输出内容格式：{"printable": {...}, "non-printable": {...}}
    """

    charSet_printable = set(c for c in charSet if (c.isprintable()))

    return {"printable":
            charSet_printable,
            "non-printable":
            charSet.difference(charSet_printable)}


def char_in_ttf(c: str, ttf: TTFont) -> bool:
    for table in ttf["cmap"].tables:
        if (ord(c) in table.cmap):
            return True
    return False


def char_in_ttc(c: str, ttc: TTCollection) -> tuple[bool, int]: #返回所在第一个字体的索引号
    for fontIndex in range(len(ttc.fonts)):
        for table in ttc.fonts[fontIndex]["cmap"].tables:
            if (ord(c) in table.cmap):
                return (True, fontIndex)
    return (False, -1)


def filter_font_support(charSet: set[str], fontPath: Path) -> dict:
    """
    区别字符在指定字体中是否有支持。
    输出内容格式：{"inFont": {...}, "not_inFont": {...}}
    """
    result = {"inFont": set(), "not_inFont": set()}
    
    if (fontPath.suffix.lower() == ".ttc"):
        ttc = TTCollection(fontPath)
        for c in charSet:
            (inTTC, ttcIndex) = char_in_ttc(c, ttc)
            if (inTTC):
                result["inFont"].add((c, ttcIndex))
            else:
                result["not_inFont"].add(c)

    else:
        ttf = TTFont(fontPath)
        for c in charSet:
            if (char_in_ttf(c, ttf)):
                result["inFont"].add(c)
            else:
                result["not_inFont"].add(c)

    return result


def main():
    cmdParser = argparse.ArgumentParser(description="读取msxx_txt生成的json文件并得出其所用字符集合的工具。")
    cmdParser.add_argument("jsonFilePath", type=Path, help="传入json文件的路径")
    cmdParser.add_argument("-o", "--out-txt", help="导出其中所有 可打印字符 到指定的纯文本文件中。所有字符将以json语言的形式打印在终端中。",
                           required=False, type=Path, default=None, dest="outTxtPath")
    cmdParser.add_argument("-f", "--font", help="字体或字体集文件。用于判断字体是否包含了某字。", required=True,
                           type=Path, dest="fontPath")
    
    args = cmdParser.parse_args()
    print(args)

    jsonFile = open(args.jsonFilePath, "rt")
    lineData = json.load(jsonFile)
    jsonFile.close()

    ########################################

    charSet_full = get_full_set(lineData)
    f_printable = filter_printable(charSet_full)
    f_inFont = filter_font_support(f_printable["printable"], args.fontPath)

    print("可打印且字体支持：\n{0}\n可打印但字体不支持：\n{1}\n不可打印字符：{2}".format(
        f_inFont["inFont"], f_inFont["not_inFont"], f_printable["non-printable"]))

    if (args.outTxtPath is not None):
        _str = []
        for i in f_inFont["inFont"]:
            if (type(i) == str):
                _str.append(i)
            elif (type(i) == tuple):
                _str.append(i[0])
        _str.sort()

        txtFile = open(args.outTxtPath, "wt")
        txtFile.write("".join(_str))
        txtFile.close()


if (__name__ == "__main__"):
    sys.exit(main())
