#!/usr/bin/env python3
"""
Generate MP3 audio files for all Italian text using edge-tts.
Creates audio/ directory with MP3 files and audio_map.json mapping.
"""
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

# Use the venv's edge-tts
sys.path.insert(0, r"C:\Users\迪丽希斯\.workbuddy\binaries\python\envs\default\Lib\site-packages")

import edge_tts

VOICE = "it-IT-ElsaNeural"  # Italian female voice
RATE = "+0%"  # Normal speed
OUTPUT_DIR = "audio"

def text_hash(text: str) -> str:
    """Generate a short unique filename for a text."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:12]

async def generate_one(text: str, sem: asyncio.Semaphore, progress: list):
    """Generate audio for one text and return the mapping entry."""
    h = text_hash(text)
    filename = f"{h}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(filepath):
        progress[0] += 1
        print(f"[{progress[0]}/{progress[1]}] ✓ (exists) {text[:40]}...")
        return (text, filename)

    async with sem:
        try:
            communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
            await communicate.save(filepath)
            progress[0] += 1
            print(f"[{progress[0]}/{progress[1]}] ✓ {text[:50]}...")
            return (text, filename)
        except Exception as e:
            progress[0] += 1
            print(f"[{progress[0]}/{progress[1]}] ✗ ERROR: {text[:50]}... -> {e}")
            return (text, None)

async def main():
    # Read all texts
    with open("_all_speak_texts.json", "r", encoding="utf-8") as f:
        texts = json.load(f)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total = len(texts)
    print(f"Generating {total} audio files using voice: {VOICE}")
    print("=" * 60)

    # Semaphore to limit concurrent requests
    sem = asyncio.Semaphore(5)
    progress = [0, total]

    # Generate all audio files
    tasks = [generate_one(text, sem, progress) for text in texts]
    results = await asyncio.gather(*tasks)

    # Build mapping (text -> filename)
    text_to_file = {}
    for text, filename in results:
        if filename:
            text_to_file[text] = filename

    # Save mapping
    mapping_path = os.path.join(OUTPUT_DIR, "audio_map.json")
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(text_to_file, f, ensure_ascii=False, indent=2)

    success = sum(1 for _, fn in results if fn)
    failed = total - success
    print(f"\n{'=' * 60}")
    print(f"Done! Generated: {success}/{total} audio files")
    print(f"Audio files: {OUTPUT_DIR}/")
    print(f"Mapping: {mapping_path}")
    if failed:
        print(f"Failed: {failed}")

if __name__ == "__main__":
    asyncio.run(main())
