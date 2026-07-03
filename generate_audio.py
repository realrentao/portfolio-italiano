# -*- coding: utf-8 -*-
"""
用 edge-tts 批量生成意语音频。

- 读取 audio_list_all.json，按版本分目录生成 MP3
- 异步并发，限制并发数 8
- 支持断点续传（已存在的文件跳过）
- 进度条 + 错误日志
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

import edge_tts

# ============================================================
# 配置
# ============================================================
WORK_DIR = Path(r"D:\workbuddy工作区\2026-07-03-21-13-45\意语作品集词汇")
AUDIO_DIR = WORK_DIR / "audio"
LIST_FILE = WORK_DIR / "audio_list_all.json"
ERROR_LOG = WORK_DIR / "audio_errors.json"

# 意大利语女声（清晰、自然）
VOICE = "it-IT-ElsaNeural"
# 语速：+0% 正常速度，-10% 稍慢便于学习
RATE = "-5%"
# 并发数
CONCURRENCY = 10


async def generate_one(text: str, output_path: Path, voice: str, rate: str, retries: int = 2) -> Exception | None:
    """生成一个音频文件。返回 None 表示成功，返回 Exception 表示失败。"""
    for attempt in range(retries + 1):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(str(output_path))
            return None
        except Exception as e:
            if attempt == retries:
                return e
            await asyncio.sleep(1.0 * (attempt + 1))
    return None


async def main():
    if not LIST_FILE.exists():
        print(f"[!] 音频清单不存在: {LIST_FILE}")
        return

    items = json.loads(LIST_FILE.read_text(encoding="utf-8"))
    total = len(items)
    print(f"[i] 共 {total} 个意语片段需要生成音频")
    print(f"[i] Voice: {VOICE}, Rate: {RATE}, Concurrency: {CONCURRENCY}")

    # 按版本分目录
    for version_id in ("basic", "enhanced", "flagship"):
        (AUDIO_DIR / version_id).mkdir(parents=True, exist_ok=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    completed = 0
    skipped = 0
    errors: list[dict] = []
    start_time = time.time()
    FORCE_REGEN = False  # 断点续传：已存在则跳过

    async def task(item: dict, idx: int):
        nonlocal completed, skipped
        async with sem:
            version = item["id"].split("_")[0]
            out_path = AUDIO_DIR / version / f"{item['id']}.mp3"

            # 断点续传：已存在则跳过（除非 FORCE_REGEN）
            if not FORCE_REGEN and out_path.exists() and out_path.stat().st_size > 0:
                skipped += 1
                completed += 1
                if completed % 50 == 0 or completed == total:
                    elapsed = time.time() - start_time
                    pct = completed / total * 100
                    rate_per_sec = completed / max(elapsed, 0.001)
                    eta = (total - completed) / max(rate_per_sec, 0.001)
                    print(f"[{completed}/{total}] {pct:5.1f}% | "
                          f"用时 {elapsed:.0f}s | 速度 {rate_per_sec:.1f}/s | "
                          f"剩余 {eta:.0f}s | 跳过 {skipped} | 错误 {len(errors)}")
                return

            err = await generate_one(item["text"], out_path, VOICE, RATE)
            if err is not None:
                errors.append({"id": item["id"], "text": item["text"], "error": str(err)})
                # 删除可能损坏的文件
                if out_path.exists():
                    try:
                        out_path.unlink()
                    except Exception:
                        pass

            completed += 1
            if completed % 50 == 0 or completed == total:
                elapsed = time.time() - start_time
                pct = completed / total * 100
                rate_per_sec = completed / max(elapsed, 0.001)
                eta = (total - completed) / max(rate_per_sec, 0.001)
                print(f"[{completed}/{total}] {pct:5.1f}% | "
                      f"用时 {elapsed:.0f}s | 速度 {rate_per_sec:.1f}/s | "
                      f"剩余 {eta:.0f}s | 跳过 {skipped} | 错误 {len(errors)}")

    tasks = [task(item, idx) for idx, item in enumerate(items)]
    await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    print(f"\n[OK] 完成！共 {completed}/{total}, 跳过 {skipped}, 错误 {len(errors)}, 用时 {elapsed:.1f}s")

    if errors:
        ERROR_LOG.write_text(
            json.dumps(errors, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[!] 错误日志: {ERROR_LOG}")
        # 重试一次失败的
        if len(errors) > 0:
            print(f"[i] 重试 {len(errors)} 个失败项...")
            retry_errors = []
            for e in errors:
                version = e["id"].split("_")[0]
                out_path = AUDIO_DIR / version / f"{e['id']}.mp3"
                err = await generate_one(e["text"], out_path, VOICE, RATE, retries=3)
                if err is not None:
                    retry_errors.append(e)
            print(f"[i] 重试后剩余失败: {len(retry_errors)}")
            if retry_errors:
                ERROR_LOG.write_text(
                    json.dumps(retry_errors, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )


if __name__ == "__main__":
    asyncio.run(main())
