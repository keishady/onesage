#!/usr/bin/env python3
"""三枚铜钱起卦：输出本卦、动爻、之卦。用法：cast.py [--seed N]"""
import random
import sys

# 先天顺序：乾兑离震巽坎艮坤；表按 [下卦][上卦] 查卦序
TRI = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
BITS = {"乾": "111", "兑": "110", "离": "101", "震": "100",
        "巽": "011", "坎": "010", "艮": "001", "坤": "000"}  # 自下而上
TABLE = [
    [1, 43, 14, 34, 9, 5, 26, 11],
    [10, 58, 38, 54, 61, 60, 41, 19],
    [13, 49, 30, 55, 37, 63, 22, 36],
    [25, 17, 21, 51, 42, 3, 27, 24],
    [44, 28, 50, 32, 57, 48, 18, 46],
    [6, 47, 64, 40, 59, 29, 4, 7],
    [33, 31, 56, 62, 53, 39, 52, 15],
    [12, 45, 35, 16, 20, 8, 23, 2],
]
NAMES = ("乾坤屯蒙需讼师比小畜履泰否同人大有谦豫随蛊临观噬嗑贲剥复无妄大畜颐大过坎离"
         "咸恒遯大壮晋明夷家人睽蹇解损益夬姤萃升困井革鼎震艮渐归妹丰旅巽兑涣节中孚小过既济未济")
NAME_LIST = ["乾", "坤", "屯", "蒙", "需", "讼", "师", "比", "小畜", "履", "泰", "否", "同人", "大有", "谦", "豫",
             "随", "蛊", "临", "观", "噬嗑", "贲", "剥", "复", "无妄", "大畜", "颐", "大过", "坎", "离", "咸", "恒",
             "遯", "大壮", "晋", "明夷", "家人", "睽", "蹇", "解", "损", "益", "夬", "姤", "萃", "升", "困", "井",
             "革", "鼎", "震", "艮", "渐", "归妹", "丰", "旅", "巽", "兑", "涣", "节", "中孚", "小过", "既济", "未济"]
LINE_NAMES = ["初", "二", "三", "四", "五", "上"]


def find(bits):  # bits: 6 个 0/1，自下而上
    lower = next(t for t in TRI if BITS[t] == "".join(map(str, bits[:3])))
    upper = next(t for t in TRI if BITS[t] == "".join(map(str, bits[3:])))
    return TABLE[TRI.index(lower)][TRI.index(upper)], upper, lower


def toss():
    """三枚铜钱：背=3 面=2。和 6=老阴(动) 7=少阳 8=少阴 9=老阳(动)"""
    return sum(random.choice((2, 3)) for _ in range(3))


def reading(moving, n1, n2):
    """读法只取《左传》《国语》筮例可证的最简规则，不用后世（如朱熹）推演的多爻变细则。"""
    k = len(moving)
    name1 = NAME_LIST[n1 - 1]
    name2 = NAME_LIST[n2 - 1] if n2 else None
    L = lambda i: LINE_NAMES[i]
    if k == 0:
        return f"无动爻：看「{name1}」卦辞；内卦为贞（自身/现状），外卦为悔（外部/变数）。"
    if k == 1:
        return f"一爻动：以「{name1}」的{L(moving[0])}爻爻辞为主；之卦「{name2}」看走向。"
    if k == 6 and n1 == 1:
        return "六爻皆动：乾卦看「用九」（见群龙无首，吉），之卦为坤。"
    if k == 6 and n1 == 2:
        return "六爻皆动：坤卦看「用六」（利永贞），之卦为乾。"
    names = "、".join(L(i) for i in moving)
    return (f"{k}爻动（{names}）：古法无统一定说。以「{name1}」为现状、之卦「{name2}」为走向，"
            f"两卦卦辞并参；动爻的爻辞作为各阶段的提示，不必强分主次。")


def main():
    if "--seed" in sys.argv:
        random.seed(int(sys.argv[sys.argv.index("--seed") + 1]))
    lines = [toss() for _ in range(6)]
    base = [1 if v in (7, 9) else 0 for v in lines]
    moving = [i for i, v in enumerate(lines) if v in (6, 9)]
    changed = [1 - b if i in moving else b for i, b in enumerate(base)]
    n1, u1, l1 = find(base)
    print(f"本卦：第{n1}卦 {NAME_LIST[n1-1]}（{u1}上{l1}下）  文件：hexagrams/{n1:02d}-{NAME_LIST[n1-1]}.md")
    n2 = None
    if moving:
        n2, u2, l2 = find(changed)
        print("动爻：" + "、".join(LINE_NAMES[i] for i in moving))
        print(f"之卦：第{n2}卦 {NAME_LIST[n2-1]}（{u2}上{l2}下）  文件：hexagrams/{n2:02d}-{NAME_LIST[n2-1]}.md")
    else:
        print("动爻：无")
    print("读法：" + reading(moving, n1, n2))


if __name__ == "__main__":
    main()
