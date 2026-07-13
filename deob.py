#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混淆方案还原工具
方案: 明文 --UTF-8--> Base64 --每个字符 +SHIFT--> 混淆串
还原: 混淆串 --每个字符 -SHIFT--> Base64 --解码--> 明文
注意: Base64 结尾的 '=' 填充符也参与了位移。
"""
import base64
import argparse

SHIFT = 5  # 加密时对每个字符 +5，还原时 -5


def deobfuscate(token: str, shift: int = SHIFT, encoding: str = "utf-8") -> str:
    """混淆串 -> 真实明文"""
    b64 = "".join(chr(ord(c) - shift) for c in token)
    # 若填充被去掉，补齐到 4 的倍数
    b64 += "=" * ((4 - len(b64) % 4) % 4)
    return base64.b64decode(b64).decode(encoding)


def obfuscate(text: str, shift: int = SHIFT, encoding: str = "utf-8") -> str:
    """真实明文 -> 混淆串"""
    b64 = base64.b64encode(text.encode(encoding)).decode("ascii")
    return "".join(chr(ord(c) + shift) for c in b64)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Base64 + 字符位移 混淆的还原/生成工具")
    p.add_argument("value", help="要处理的字符串")
    p.add_argument("-e", "--encode", action="store_true", help="生成混淆串(默认是还原)")
    p.add_argument("-s", "--shift", type=int, default=SHIFT, help="位移量(默认5)")
    p.add_argument("--enc", default="utf-8", help="文本编码(默认utf-8, 可试gbk)")
    a = p.parse_args()

    if a.encode:
        print(obfuscate(a.value, a.shift, a.enc))
    else:
        print(deobfuscate(a.value, a.shift, a.enc))
