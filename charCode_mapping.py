from typing import Tuple, Iterable


class CharCode():
    """
    与FontLib中，字符unicode码、mainMappingTable、specialCharTable专门相关的类
    """
    Boundary = (0x00FF, 0x2BFF, 0x2E7F, 0x9FFF,
                0xFDFF, 0xFFFF)  # 预设的012345，6个区间的界线
    # 非特殊符号的区间长
    NormalAreaLen = (Boundary[5] - Boundary[4]) + (Boundary[3] -
                                                   Boundary[2]) + (Boundary[0] - 0x0000)

    def __init__(self):
        self.specialCharTable = []  # specialCharTable本身就记载unicode值

        # 记载specialCharTable中各字在charInfoTable中的下标值，追加在mainMappingTable Normal区之后
        self.specialCharTable_charInfoIndex = []
        self.mainMappingTable_normal = [
            65535 for _ in range(self.NormalAreaLen)]

    def get_area(self, code: int) -> int:
        """
        根据unicode码计算字区号
        """
        if (not 0 <= code <= 0xFFFF):
            raise ValueError(
                "不在支持的unicode码范围内([0x0000, 0xFFFF])，你传入了：0x{0:x}".format(code))

        for i in range(len(self.Boundary)):
            if (code <= self.Boundary[i]):
                return i

    def get_area_range(self, areaID: int) -> Tuple[int, int]:
        """
        根据分区号给出unicode码的范围
        """
        if (areaID not in range(0, 6)):
            raise ValueError("不支持的范围号：{0:n}".format(areaID))

        if (areaID == 0):
            return (0, self.Boundary[0])
        else:
            return (self.Boundary[areaID - 1], self.Boundary[areaID])

    # def get_mainMappingTable_index(self, code: int, specialCharTable: Iterable[int]) -> int:
    def get_mainMappingTable_index(self, code: int) -> int:
        """
        传入unicode码，计算其在主映射表中该对应的下标值
        """
        areaID = self.get_area(code)
        (m, M) = self.get_area_range(areaID)

        match (areaID):
            case 0:
                return code
            case 1 | 2 | 4:
                for i in range(len(self.specialCharTable)):
                    if (self.specialCharTable[i] == code):
                        return + i  # i之前的长度都是作为非特殊符号的区间的长度
            case 3:
                return (self.Boundary[0] - 0x0000) + (code - m)
            case 5:
                return (self.NormalAreaLen - (self.Boundary[5] - self.Boundary[4])) + (code - m)
            case _:
                raise ValueError("未知范围号：{0:n}".format(areaID))

    def import_char(self, charInfoList_code: Iterable[int]):
        """
        传入只有unicode码的charInfoList
        """
        for i in range(len(charInfoList_code)):
            c = charInfoList_code[i]
            match (self.get_area(c)):
                case 0 | 3 | 5:
                    self.mainMappingTable_normal[self.get_mainMappingTable_index(
                        c)] = i
                case 1 | 2 | 4:
                    self.specialCharTable.append(c)
                    self.specialCharTable_charInfoIndex.append(i)
                case _:
                    raise ValueError("未知范围号：{0:n}".format(areaID))

    def get_mainMappingTable(self) -> list[int]:
        return self.mainMappingTable_normal + self.specialCharTable_charInfoIndex

    def get_specialCharTable(self) -> list[int]:
        return self.specialCharTable
