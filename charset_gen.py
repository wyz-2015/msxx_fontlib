#!/usr/bin/env python3

import json
import argparse
from pathlib import Path
import sys


def get_char_set(lineData: dict) -> dict:
    """
    输出内容格式：{"printable": "...", "non-printable": "..."}
    """
    charSet_full = set()

    for blockSet in lineData:
        for block in blockSet["blockList"]:
            for _str in block["strList"]:
                for c in _str:
                    charSet_full.add(c)

    # charSet_list = sorted(charSet_raw)
    charSet_printable = set(c for c in charSet_full if (c.isprintable()))

    return {"printable":
            "".join(sorted(charSet_printable)),
            "non-printable":
            "".join(sorted(charSet_full.difference(charSet_printable)))}


def main():
    cmdParser = argparse.ArgumentParser(description="读取msxx_txt生成的json文件并得出其所用字符集合的工具。")
    cmdParser.add_argument("jsonFilePath", type=Path, help="传入json文件的路径")
    cmdParser.add_argument("-o", "--out-txt", help="导出其中所有 可打印字符 到指定的纯文本文件中。所有字符将以json语言的形式打印在终端中。",
                           required=False, type=Path, default=None, dest="outTxtPath")
    
    args = cmdParser.parse_args()

    jsonFile = open(args.jsonFilePath, "rt")
    lineData = json.load(jsonFile)
    jsonFile.close()

    charSet_filtered = get_char_set(lineData)

    print(json.dumps(charSet_filtered, ensure_ascii=False, indent='\t'))

    if (args.outTxtPath is not None):
        txtFile = open(args.outTxtPath, "wt")
        txtFile.write(charSet_filtered["printable"])
        txtFile.close()


if (__name__ == "__main__"):
    sys.exit(main())
