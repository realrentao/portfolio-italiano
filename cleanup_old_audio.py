# -*- coding: utf-8 -*-
"""清理旧的顺序 id 音频文件（如 basic_0001.mp3），保留 hash id 文件（如 basic_a1b2c3d4.mp3）。"""
import os
import re
from pathlib import Path

AUDIO_DIR = Path(r"D:\workbuddy工作区\2026-07-03-21-13-45\意语作品集词汇\audio")
# 旧的顺序 id 格式：basic_0001, enhanced_0099 等
OLD_ID_PATTERN = re.compile(r"^(basic|enhanced|flagship)_\d{4}\.mp3$")

removed = 0
kept = 0
for sub in ["basic", "enhanced", "flagship"]:
    sub_dir = AUDIO_DIR / sub
    if not sub_dir.exists():
        continue
    for f in sub_dir.iterdir():
        if f.is_file() and f.suffix == ".mp3":
            if OLD_ID_PATTERN.match(f.name):
                try:
                    os.remove(str(f))
                    removed += 1
                except Exception as e:
                    print(f"Error removing {f.name}: {e}")
            else:
                kept += 1

print(f"Removed old sequential-id files: {removed}")
print(f"Kept hash-id files: {kept}")
