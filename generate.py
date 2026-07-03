# -*- coding: utf-8 -*-
"""
基于三个 markdown 文件生成意大利语作品集词汇教学页面（基础版/加强版/旗舰版 + 导航页）。

- 统一 UI 风格（深色主题 + 意大利国旗色点缀）
- 各版本保留特色色（基础版绿 / 加强版金 / 旗舰版紫）
- 意大利语部分支持点击播放（音频文件由 generate_audio.py 用 edge-tts 生成）
"""
from __future__ import annotations

import json
import re
import hashlib
import html as html_lib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# ============================================================
# 配置
# ============================================================
WORK_DIR = Path(r"D:\workbuddy工作区\2026-07-03-21-13-45\意语作品集词汇")
SOURCE_DIR = Path(r"D:/")
AUDIO_DIR = WORK_DIR / "audio"

VERSIONS: List[Dict[str, Any]] = [
    {
        "id": "basic",
        "name": "基础版",
        "name_it": "Fondamenti",
        "tagline": "从零开始，能开口介绍作品集",
        "source": "🇮🇹 设计留学作品集·意语词汇（基础版）.md",
        "accent": "#10b981",
        "accent_soft": "rgba(16, 185, 129, 0.15)",
        "glow": "rgba(16, 185, 129, 0.35)",
        "icon": "🌱",
        "description": "面向 A1-A2 水平同学。掌握作品集介绍必备词汇、设计流程三件套、面试高频句型，30 天张嘴就能说。",
        "level": "A1-A2",
        "study_time": "30 天",
        "highlights": ["基础词汇 50+", "万能句型 10+", "30 天学习路径"],
    },
    {
        "id": "enhanced",
        "name": "加强版",
        "name_it": "Intermedio",
        "tagline": "分科词汇 + 深度句型 + 面试模拟",
        "source": "🇮🇹 设计留学作品集·意语词汇（加强版）.md",
        "accent": "#f59e0b",
        "accent_soft": "rgba(245, 158, 11, 0.15)",
        "glow": "rgba(245, 158, 11, 0.35)",
        "icon": "🚀",
        "description": "面向 A2-B1 水平同学。按 7 大设计方向分科词汇，含完整面试问答模版和 5 分钟作品集介绍实战。",
        "level": "A2-B1",
        "study_time": "30 天",
        "highlights": ["7 大设计方向", "面试 10 问 + 模版", "5 分钟完整介绍"],
    },
    {
        "id": "flagship",
        "name": "旗舰版",
        "name_it": "Avanzato",
        "tagline": "名校攻略 + 设计文化 + 学术高阶",
        "source": "🇮🇹 设计留学作品集·意语词汇（旗舰版）.md",
        "accent": "#a855f7",
        "accent_soft": "rgba(168, 85, 247, 0.15)",
        "glow": "rgba(168, 85, 247, 0.35)",
        "icon": "👑",
        "description": "面向 B1-C1 水平同学。米理/都理/IUAV 等名校风格解码，含设计大师谈资、学术批评词汇、高级语法。",
        "level": "B1-C1",
        "study_time": "30 天",
        "highlights": ["6 所名校攻略", "6 位设计大师", "学术批评高阶词汇"],
    },
]

# 意语特征词（用于启发式判断一段文本是否为意大利语）
IT_INDICATORS = re.compile(
    r"\b(il|la|lo|l'|gli|le|un|una|un'|di|del|della|dei|che|per|con|sono|ho|ha|"
    r"abbiamo|avete|hanno|è|in|al|alla|dal|dalla|mi|ti|si|ci|vi|li|la|lo|"
    r"questo|questa|quello|quella|come|perché|quando|dove|chi|cosa|quale|"
    r"molto|poco|bene|male|oggi|domani|sempre|mai|anche|solo|così|"
    r"ho|fatto|creato|sviluppato|presento|voglio|vorrei|penso|credo|"
    r"design|progetto|portfolio|concept|research|user|target|"
    r"ricerca|ispirazione|modellazione|prototipo|schizzo|bozzetto|"
    r"dissegno|sviluppo|revisione|sperimentazione|collezione|opera|"
    r"soluzione|installazione|materiale|sostenibile)\b",
    re.IGNORECASE,
)

# 常见意大利语词尾（用于检测单词语音片段）
ITALIAN_SUFFIX = re.compile(
    r"(ale|ico|ica|ile|ivo|iva|one|ino|ina|ato|ata|ente|enza|"
    r"zione|mento|tore|trice|ista|abile|ibile|"
    r"ico|ica|ido|ida|ile|ino|ona|ore|ice|"
    r"ismo|ista|logia|grafia|metria|fia|"
    r"tà|sione|cione|ggiare|izzare)$",
    re.IGNORECASE,
)


# ============================================================
# Markdown 解析
# ============================================================
def parse_markdown(text: str) -> List[Dict[str, Any]]:
    """把 markdown 文本解析为块列表。

    支持的块类型：
      - h1/h2/h3/h4   标题
      - hr             分隔线
      - code           代码块
      - table          表格 {headers, rows, italian_cols}
      - quote          引用块 {lines: [...]}
      - list           列表 {items: [...]}
      - p              普通段落
    """
    lines = text.split("\n")
    blocks: List[Dict[str, Any]] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 空行
        if not stripped:
            i += 1
            continue

        # 分隔线
        if stripped in ("***", "---", "___"):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # 代码块
        if stripped.startswith("```"):
            code_lines: List[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing
            blocks.append({"type": "code", "content": "\n".join(code_lines)})
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if m:
            level = len(m.group(1))
            content = m.group(2).strip()
            blocks.append({"type": f"h{level}", "content": content})
            i += 1
            continue

        # 表格
        if stripped.startswith("|"):
            table_lines: List[str] = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            blocks.append({"type": "table", **parse_table(table_lines)})
            continue

        # 引用块
        if stripped.startswith(">"):
            quote_lines: List[str] = []
            while i < n and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append({"type": "quote", "lines": quote_lines})
            continue

        # 无序列表
        if re.match(r"^[-*]\s+", stripped):
            items: List[str] = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            blocks.append({"type": "list", "items": items})
            continue

        # 有序列表
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            blocks.append({"type": "olist", "items": items})
            continue

        # 普通段落（连续非空非块行）
        para_lines = []
        while i < n:
            cur = lines[i].strip()
            if not cur:
                break
            if cur.startswith(("#", "|", ">", "```", "***", "---", "___")):
                break
            if re.match(r"^[-*]\s+", cur) or re.match(r"^\d+\.\s+", cur):
                break
            para_lines.append(cur)
            i += 1
        if para_lines:
            blocks.append({"type": "p", "content": "\n".join(para_lines)})

    return blocks


def parse_table(lines: List[str]) -> Dict[str, Any]:
    """解析表格行，识别哪些列是意语。"""
    rows: List[List[str]] = []
    for line in lines:
        # 跳过分隔行
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return {"headers": [], "rows": [], "italian_cols": []}

    headers = rows[0]
    body = rows[1:]

    # 识别意语列
    italian_cols: List[int] = []
    for col_idx, header in enumerate(headers):
        header_lower = header.lower().strip("* ")
        # 表头明确标识为意语（只认这两个，避免误判）
        if any(k in header_lower for k in ("意大利语", "意语")):
            italian_cols.append(col_idx)
            continue
        # 表头为例句/设计语境/解释 → 内容可能是意语
        if any(k in header_lower for k in ("例句", "设计语境", "解释")):
            # 进一步判断该列内容是否真有意语
            col_content = " ".join((r[col_idx] if col_idx < len(r) else "") for r in body)
            if _is_italian(col_content):
                italian_cols.append(col_idx)
            continue
        # 表头为反义词 → 内容可能是意语
        if "反义" in header_lower:
            col_content = " ".join((r[col_idx] if col_idx < len(r) else "") for r in body)
            if _is_italian(col_content):
                italian_cols.append(col_idx)
            continue
        # 表头是中文，且该列内容主要是意语
        if header_lower and not _is_italian(header_lower):
            col_content = " ".join((r[col_idx] if col_idx < len(r) else "") for r in body)
            if _is_italian(col_content):
                italian_cols.append(col_idx)

    return {"headers": headers, "rows": body, "italian_cols": italian_cols}


def _is_italian(text: str) -> bool:
    """启发式判断一段文本是否主要为意大利语。"""
    if not text:
        return False
    # 去除 markdown 标记
    cleaned = re.sub(r"[_*`]", "", text)
    # 去除中文
    cleaned_no_cn = re.sub(r"[\u4e00-\u9fff]+", " ", cleaned)
    if not cleaned_no_cn.strip():
        return False
    # 中文字符占比高 → 不是意语（阈值收紧到 20%）
    cn_chars = len(re.findall(r"[\u4e00-\u9fff]", cleaned))
    # 只算"实质"字符（字母+中文，忽略空白和标点）
    alpha_chars = len(re.findall(r"[a-zA-ZàèéìòùÀÈÉÌÒÙ]", cleaned))
    total_meaningful = cn_chars + alpha_chars
    if total_meaningful > 0 and cn_chars / total_meaningful > 0.20:
        return False

    # 提取纯意语单词（去掉标点符号）
    words = re.findall(r"[a-zA-ZàèéìòùÀÈÉÌÒÙ]+", cleaned_no_cn)
    if not words:
        return False

    # 检查意语特征词
    matches = IT_INDICATORS.findall(cleaned_no_cn)
    ratio = len(matches) / max(len(words), 1)

    # 有足够的特征词匹配 → 是意语
    if ratio > 0.15 or len(matches) >= 2:
        return True

    # 单个单词或少数单词：检查词尾是否为意语特征词尾
    # 例如 minimale, moderno, sostenibile, elegante 等
    for word in words:
        if re.search(r"(ale|ico|ica|ile|ivo|iva|one|ino|ina|ato|ata|"
                     r"ente|enza|zione|mento|tore|trice|ista|abile|ibile|"
                     r"ismo|tà|ore|ice|logia|grafia|metria)$", word, re.IGNORECASE):
            return True

    # 第二层词尾检查：常见意语形容词/名词结尾（要求单词至少4个字符避免误判）
    for word in words:
        wl = len(word)
        if wl >= 4 and re.search(r"(ano|ato|ido|olo|ogo|ero|"
                                 r"ale|ile|ino|ona|"
                                 r"cco|llo|nno|rio|"
                                 r"nza|zia|cia|gia|ggio|tto)$", word, re.IGNORECASE):
            return True
        # 更短的双字母词尾，需要更长单词保证精确度
        if wl >= 5 and re.search(r"(no|do|lo|eo|co|go|so|"
                                 r"ca|pa|ffa|mma)$", word, re.IGNORECASE):
            return True

    # 检查是否包含常见意语动词形式
    verb_pattern = re.compile(r"\b\w+(ato|ata|iti|ite|endo|ando|ire|ere|are|isco|isci|isce|iamo|ite|ono)$", re.IGNORECASE)
    for word in words:
        if verb_pattern.match(word):
            return True

    return False


# ============================================================
# 意语片段收集（全局，用于生成音频清单）
# ============================================================
class AudioCollector:
    """收集所有需要 TTS 的意语片段，生成唯一 ID。"""

    def __init__(self, version_id: str):
        self.version_id = version_id
        self.items: List[Dict[str, str]] = []
        self._seen: Dict[str, str] = {}  # text -> id

    def add(self, text: str) -> str:
        """注册一段意语，返回 audio_id。重复文本会复用同一个 id。

        使用基于文本内容的 hash 作为 id，保证相同文本总是对应相同文件名。
        如果文本不是意语（纯中文/空/太短），返回空字符串。
        """
        # 清理 markdown 标记
        clean = self._clean_text(text)
        if not clean.strip():
            return ""
        # 过滤掉零宽字符等
        clean = clean.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "").strip()
        if not clean:
            return ""
        # 必须包含至少一个拉丁字母（意语的基本特征）
        if not re.search(r"[a-zA-ZàèéìòùÀÈÉÌÒÙ]", clean):
            return ""
        # 用启发式判断是否为意语
        if not _is_italian(clean):
            return ""
        if clean in self._seen:
            return self._seen[clean]
        # 基于 text 内容生成 hash id（前 8 位 md5）
        text_hash = hashlib.md5(clean.encode("utf-8")).hexdigest()[:8]
        audio_id = f"{self.version_id}_{text_hash}"
        self._seen[clean] = audio_id
        self.items.append({"id": audio_id, "text": clean})
        return audio_id

    @staticmethod
    def _clean_text(text: str) -> str:
        """清理 markdown 标记和 HTML 实体，保留纯意语文本。"""
        # 先解 HTML 实体（&#x27; → ' 等），防止其对意语特征词匹配的影响
        s = html_lib.unescape(text)
        # 去掉行内代码标记
        s = re.sub(r"`([^`]+)`", r"\1", s)
        # 去掉粗体/斜体标记
        s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
        s = re.sub(r"\*([^*]+)\*", r"\1", s)
        s = re.sub(r"_([^_]+)_", r"\1", s)
        # 去掉方括号占位符 [xxx]
        s = re.sub(r"\[([^\]]+)\]", r"\1", s)
        # 去掉反斜杠转义
        s = s.replace("\\", "")
        # 合并空白
        s = re.sub(r"\s+", " ", s).strip()
        return s


# ============================================================
# 行内格式渲染
# ============================================================
def replace_italian_flag_emoji(text: str) -> str:
    """把 🇮🇹 emoji 替换为 CSS 国旗图标 HTML（Windows 不支持国旗 emoji 彩色显示）。"""
    if not text:
        return text
    # 🇮🇹 是由 U+1F1EE (🇮) + U+1F1F9 (🇹) 两个区域指示符组成
    return text.replace("\U0001f1ee\U0001f1f9", '<span class="it-flag"></span>')


def render_inline(text: str, collector: AudioCollector) -> str:
    """渲染行内 markdown：粗体、斜体、行内代码、链接等。

    意语片段（在斜体 `_xxx_` 中的）会被注册为可播放音频。
    """
    if not text:
        return ""

    # 替换意大利国旗 emoji
    text = replace_italian_flag_emoji(text)

    # 先处理行内代码 `xxx`
    placeholders: Dict[str, str] = {}

    def stash(match: re.Match) -> str:
        key = f"\x00CODE{len(placeholders)}\x00"
        inner = match.group(1)
        # 行内代码用 <code> 包裹
        placeholders[key] = f'<code class="inline-code">{html_lib.escape(inner)}</code>'
        return key

    text = re.sub(r"`([^`]+)`", stash, text)

    # 处理斜体 _xxx_ 或 *xxx*（但 ** 优先匹配粗体）
    def italic_repl(match: re.Match) -> str:
        inner = match.group(1).strip()
        audio_id = collector.add(inner)
        if audio_id:
            return (
                f'<span class="it-text" data-audio="{audio_id}">'
                f'<span class="it-word">{html_lib.escape(inner)}</span>'
                f'<button class="play-btn" data-audio="{audio_id}" '
                f'aria-label="播放" title="点击播放">🔊</button>'
                f"</span>"
            )
        return f'<em>{html_lib.escape(inner)}</em>'

    # 注意：先匹配 **粗体**，再匹配 _斜体_ 和 *斜体*
    # 粗体 **xxx**
    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: f'<strong>{html_lib.escape(m.group(1))}</strong>', text)
    # 斜体 _xxx_（更常见于意语）
    text = re.sub(r"_([^_]+)_", italic_repl, text)
    # 斜体 *xxx*（避免和粗体冲突，要求前后不是 *）
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", italic_repl, text)

    # 恢复行内代码
    for key, val in placeholders.items():
        text = text.replace(key, val)

    # 处理普通文本中的 HTML 转义（注意：已经处理过的标签不要再转义）
    # 这里用一个简单方法：用占位符保护已生成的 HTML 标签
    return text


def render_inline_plain(text: str, collector: AudioCollector, force_audio: bool = False) -> str:
    """渲染整段都是意语的文本（表格单元格、引用块等）。

    与 render_inline 不同：当文本本身被识别为意语时，整段注册为可播放音频。
    """
    if not text:
        return ""

    # 替换意大利国旗 emoji
    text = replace_italian_flag_emoji(text)

    # 处理行内代码
    placeholders: Dict[str, str] = {}

    def stash(match: re.Match) -> str:
        key = f"\x00CODE{len(placeholders)}\x00"
        inner = match.group(1)
        placeholders[key] = f'<code class="inline-code">{html_lib.escape(inner)}</code>'
        return key

    text = re.sub(r"`([^`]+)`", stash, text)

    # 处理斜体（嵌套在意语中的斜体）
    def italic_repl(match: re.Match) -> str:
        inner = match.group(1).strip()
        audio_id = collector.add(inner)
        if audio_id:
            return (
                f'<span class="it-text" data-audio="{audio_id}">'
                f'<span class="it-word">{html_lib.escape(inner)}</span>'
                f'<button class="play-btn" data-audio="{audio_id}" '
                f'aria-label="播放" title="点击播放">🔊</button>'
                f"</span>"
            )
        return f'<em>{html_lib.escape(inner)}</em>'

    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: f'<strong>{html_lib.escape(m.group(1))}</strong>', text)
    text = re.sub(r"_([^_]+)_", italic_repl, text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", italic_repl, text)

    # 如果还有剩余纯文本，并且 force_audio=True，整段注册为音频
    # 这里我们检查：如果文本里还有未包裹的意语内容（即没有 HTML 标签），整段作为音频
    has_html_tag = "<" in text and ">" in text
    if force_audio and not has_html_tag:
        audio_id = collector.add(text)
        if audio_id:
            clean = collector._clean_text(text)
            text = (
                f'<span class="it-text" data-audio="{audio_id}">'
                f'<span class="it-word">{html_lib.escape(clean)}</span>'
                f'<button class="play-btn" data-audio="{audio_id}" '
                f'aria-label="播放" title="点击播放">🔊</button>'
                f"</span>"
            )
    elif force_audio and has_html_tag:
        # 已有内层 it-text（播放按钮）则不添加外层整段按钮，避免重复
        if 'it-text' in text:
            pass  # 保留当前 text，不加外层包裹
        else:
            # 没有内层播放按钮的整段意语，添加外层播放按钮
            plain = re.sub(r"<[^>]+>", "", text)
            plain = re.sub(r"\s+", " ", plain).strip()
            if plain:
                audio_id = collector.add(plain)
                if audio_id:
                    text = (
                        f'<span class="it-text it-text-block" data-audio="{audio_id}">'
                        f'{text}'
                        f'<button class="play-btn play-btn-block" data-audio="{audio_id}" '
                        f'aria-label="播放整段" title="点击播放整段">🔊</button>'
                        f"</span>"
                    )

    # 恢复行内代码
    for key, val in placeholders.items():
        text = text.replace(key, val)

    return text


# ============================================================
# 块渲染
# ============================================================
def render_blocks(blocks: List[Dict[str, Any]], collector: AudioCollector, version: Dict[str, Any]) -> str:
    """把块列表渲染为 HTML。"""
    parts: List[str] = []
    toc_entries: List[Dict[str, str]] = []
    section_counter = [0]  # 所有标题的 sid 计数（保证唯一）
    h1_counter = [0]       # 只为 H1 编号（显示用）
    # 用于识别第一个与版本名重复的 H1（hero 已展示版本信息，跳过避免冗余）
    version_keyword = version["name"]  # 如 "基础版"
    skipped_first_h1 = [False]

    for block in blocks:
        t = block["type"]
        if t == "h1":
            section_counter[0] += 1
            # 跳过第一个与版本名重复的 H1
            if not skipped_first_h1[0] and version_keyword in block["content"]:
                skipped_first_h1[0] = True
                continue
            h1_counter[0] += 1
            sid = f"sec-{section_counter[0]}"
            title = strip_md(block["content"])
            toc_entries.append({"id": sid, "title": title, "level": "1"})
            parts.append(
                f'<h1 id="{sid}" class="section-title">'
                f'<span class="section-number">{h1_counter[0]:02d}</span>'
                f'<span class="section-title-text">{render_inline(block["content"], collector)}</span>'
                f"</h1>"
            )
        elif t == "h2":
            section_counter[0] += 1
            sid = f"sec-{section_counter[0]}"
            title = strip_md(block["content"])
            toc_entries.append({"id": sid, "title": title, "level": "2"})
            parts.append(f'<h2 id="{sid}" class="subsection-title">{render_inline(block["content"], collector)}</h2>')
        elif t == "h3":
            section_counter[0] += 1
            sid = f"sec-{section_counter[0]}"
            title = strip_md(block["content"])
            toc_entries.append({"id": sid, "title": title, "level": "3"})
            parts.append(f'<h3 id="{sid}" class="subsubsection-title">{render_inline(block["content"], collector)}</h3>')
        elif t == "h4":
            parts.append(f'<h4 class="h4-title">{render_inline(block["content"], collector)}</h4>')
        elif t == "h5":
            parts.append(f'<h5 class="h5-title">{render_inline(block["content"], collector)}</h5>')
        elif t == "h6":
            parts.append(f'<h6 class="h6-title">{render_inline(block["content"], collector)}</h6>')
        elif t == "hr":
            parts.append('<div class="divider"></div>')
        elif t == "code":
            parts.append(f'<pre class="code-block"><code>{html_lib.escape(block["content"])}</code></pre>')
        elif t == "table":
            parts.append(render_table(block, collector))
        elif t == "quote":
            parts.append(render_quote(block, collector))
        elif t == "list":
            parts.append(render_list(block, collector, ordered=False))
        elif t == "olist":
            parts.append(render_list(block, collector, ordered=True))
        elif t == "p":
            parts.append(f'<p class="paragraph">{render_inline(block["content"], collector)}</p>')

    # 把 TOC 注入到 parts 头部（用占位符）
    toc_html = render_toc(toc_entries, version)
    return toc_html + "\n".join(parts)


def strip_md(text: str) -> str:
    """去除 markdown 标记，返回纯文本（用于 TOC）。"""
    s = re.sub(r"`([^`]+)`", r"\1", text)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r"_([^_]+)_", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    # 去除意大利国旗 emoji（TOC 里不显示）
    s = s.replace("\U0001f1ee\U0001f1f9", "")
    return s.strip()


def render_toc(entries: List[Dict[str, str]], version: Dict[str, Any]) -> str:
    """渲染侧边目录（用 <nav> 包裹，会在页面侧边显示）。"""
    if not entries:
        return ""
    items = []
    for e in entries:
        cls = f"toc-item toc-level-{e['level']}"
        items.append(f'<a href="#{e["id"]}" class="{cls}">{html_lib.escape(e["title"])}</a>')
    return f'<nav class="toc-sidebar" id="tocSidebar"><div class="toc-title">目录</div>{"".join(items)}</nav>'


def render_table(block: Dict[str, Any], collector: AudioCollector) -> str:
    headers = block.get("headers", [])
    rows = block.get("rows", [])
    italian_cols = set(block.get("italian_cols", []))

    if not headers:
        return ""

    # 表头
    th_cells = []
    for idx, h in enumerate(headers):
        th_cells.append(f"<th>{html_lib.escape(strip_md(h))}</th>")
    thead = f'<thead><tr>{"".join(th_cells)}</tr></thead>'

    # 表体
    trs = []
    for row in rows:
        tds = []
        for idx, cell in enumerate(row):
            if idx in italian_cols:
                # 整个单元格作为意语可播放
                cell_html = render_inline_plain(cell, collector, force_audio=True)
                tds.append(f'<td class="it-cell">{cell_html}</td>')
            else:
                tds.append(f'<td>{render_inline(cell, collector)}</td>')
        trs.append(f'<tr>{"".join(tds)}</tr>')
    tbody = f'<tbody>{"".join(trs)}</tbody>'

    return f'<div class="table-wrap"><table class="data-table">{thead}{tbody}</table></div>'


def render_quote(block: Dict[str, Any], collector: AudioCollector) -> str:
    """渲染引用块。

    - 如果引用块整体是意语，整段作为可播放音频
    - 否则逐行判断：意语行加播放按钮，中文行正常显示
    """
    lines = block.get("lines", [])
    if not lines:
        return ""

    # 合并为一个文本，但保留换行
    full_text = "\n".join(lines)

    # 判断整段是否为意语（取第一行或所有内容）
    is_it = _is_italian(full_text)

    # 渲染每行
    rendered_lines = []
    for line in lines:
        if is_it:
            rendered_lines.append(render_inline_plain(line, collector, force_audio=True))
        else:
            # 逐行判断：如果是意语行，加播放按钮
            if _is_italian(line):
                rendered_lines.append(render_inline_plain(line, collector, force_audio=True))
            else:
                rendered_lines.append(render_inline(line, collector))

    cls = "quote-block quote-italian" if is_it else "quote-block"
    return f'<blockquote class="{cls}">{"".join(rendered_lines)}</blockquote>'


def render_list(block: Dict[str, Any], collector: AudioCollector, ordered: bool = False) -> str:
    items = block.get("items", [])
    if not items:
        return ""
    tag = "ol" if ordered else "ul"
    cls = "list-block" + (" list-ordered" if ordered else "")
    lis = []
    for item in items:
        lis.append(f"<li>{render_inline(item, collector)}</li>")
    return f'<{tag} class="{cls}">{"".join(lis)}</{tag}>'


# ============================================================
# HTML 页面模板
# ============================================================
def build_html(version: Dict[str, Any], blocks: List[Dict[str, Any]], collector: AudioCollector) -> str:
    """生成单个版本的完整 HTML 页面。"""
    body_html = render_blocks(blocks, collector, version)

    # 找其他版本用于导航
    others = [v for v in VERSIONS if v["id"] != version["id"]]

    # 顶部导航：版本切换
    nav_items = []
    for v in VERSIONS:
        active = "active" if v["id"] == version["id"] else ""
        nav_items.append(
            f'<a href="{v["id"]}.html" class="version-switch-btn {active}" '
            f'style="--btn-accent: {v["accent"]}; --btn-glow: {v["glow"]}">'
            f'<span class="vsw-icon">{v["icon"]}</span>'
            f'<span class="vsw-name">{v["name"]}</span>'
            f"</a>"
        )

    # 页头信息卡片
    header_card = f"""
    <section class="hero" style="--accent: {version["accent"]}; --accent-soft: {version["accent_soft"]}; --glow: {version["glow"]};">
      <div class="hero-bg-flag"></div>
      <div class="hero-content">
        <div class="hero-icon">{version["icon"]}</div>
        <div class="hero-text">
          <div class="hero-eyebrow">
            <span class="hero-version">VOCABOLARIO · {version["name_it"]}</span>
            <span class="hero-level">水平 {version["level"]}</span>
            <span class="hero-time">学习周期 {version["study_time"]}</span>
          </div>
          <h1 class="hero-title">设计留学作品集 · 意语词汇 <span class="hero-version-tag">{version["name"]}</span></h1>
          <p class="hero-tagline">{version["tagline"]}</p>
          <p class="hero-desc">{version["description"]}</p>
          <div class="hero-highlights">
            {''.join(f'<span class="hl-chip"><span class="hl-dot"></span>{h}</span>' for h in version["highlights"])}
          </div>
        </div>
      </div>
    </section>
    """

    # 返回导航
    bottom_nav = f"""
    <nav class="bottom-nav">
      <a href="index.html" class="bn-home">
        <span class="bn-icon">🏠</span>
        <span class="bn-text">返回导航页</span>
      </a>
      <div class="bn-others">
        {''.join(
            f'<a href="{v["id"]}.html" class="bn-other" style="--btn-accent: {v["accent"]};">'
            f'<span class="bno-icon">{v["icon"]}</span>'
            f'<span class="bno-name">前往{v["name"]}</span>'
            f'<span class="bno-arrow">→</span>'
            f'</a>'
            for v in others
        )}
      </div>
    </nav>
    """

    # 顶部固定导航栏
    topbar = f"""
    <header class="topbar" style="--accent: {version["accent"]};">
      <div class="topbar-inner">
        <a href="index.html" class="topbar-home" aria-label="返回导航页">
          <span class="it-flag it-flag-lg"></span>
          <span class="tb-title">设计留学 · 意语词汇</span>
        </a>
        <nav class="topbar-version-switch">{''.join(nav_items)}</nav>
        <button class="topbar-toc-toggle" id="tocToggle" aria-label="切换目录">
          <span class="toc-icon">☰</span>
          <span class="toc-label">目录</span>
        </button>
      </div>
    </header>
    """

    # 顶部快速统计
    stats_bar = f"""
    <div class="stats-bar" style="--accent: {version["accent"]};">
      <div class="stat-item">
        <span class="stat-num">{len(collector.items)}</span>
        <span class="stat-label">意语片段</span>
      </div>
      <div class="stat-item">
        <span class="stat-num">点击</span>
        <span class="stat-label">🔊 即可播放</span>
      </div>
      <div class="stat-item">
        <span class="stat-num">A-Z</span>
        <span class="stat-label">支持搜索</span>
      </div>
    </div>
    """

    # 主结构
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>设计留学作品集 · 意语词汇（{version["name"]}）</title>
<style>{COMMON_CSS}</style>
<style>{get_version_css(version)}</style>
</head>
<body data-version="{version["id"]}" data-accent="{version["accent"]}">
{topbar}
<main class="page-main">
  <div class="main-grid">
    {body_html.split('<nav class="toc-sidebar"', 1)[0] if '<nav class="toc-sidebar"' in body_html else ''}
    {'<nav class="toc-sidebar"' + body_html.split('<nav class="toc-sidebar"', 1)[1] if '<nav class="toc-sidebar"' in body_html else ''}
  </div>
</main>
"""
    # 上面的写法有点 hack，重写一下：把 TOC 单独抽出来
    # 实际上 render_blocks 已经把 toc 放在最前面，我们直接用 body_html
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>设计留学作品集 · 意语词汇（{version["name"]}）</title>
<meta name="description" content="{version["tagline"]} - 赴意大利留学生设计作品集意语词汇教程">
<style>{COMMON_CSS}</style>
<style>{get_version_css(version)}</style>
</head>
<body data-version="{version["id"]}" data-accent="{version["accent"]}">
{topbar}
<main class="page-main">
  <div class="main-container">
    {header_card}
    {stats_bar}
    <div class="main-grid">
      {body_html}
    </div>
  </div>
</main>
{bottom_nav}
<button class="back-to-top" id="backToTop" aria-label="返回顶部" title="返回顶部">
  <span>↑</span>
</button>
<div class="audio-player-toast" id="playerToast" hidden>
  <span class="toast-icon">🔊</span>
  <span class="toast-text">正在播放...</span>
</div>
<script>{COMMON_JS}</script>
</body>
</html>
"""
    return html


# ============================================================
# CSS
# ============================================================
COMMON_CSS = r"""
:root {
  /* 浅色主题 */
  --bg-primary: #f5f6f8;
  --bg-secondary: #ffffff;
  --bg-tertiary: #eef0f4;
  --bg-card: #ffffff;
  --bg-card-hover: #f0f2f6;
  --bg-elevated: #f8f9fb;
  --text-primary: #1a1d2e;
  --text-secondary: #4a5170;
  --text-muted: #7a82a0;
  --text-dim: #9aa0b8;
  --border-color: #d8dce4;
  --border-soft: #e6e9f0;

  /* 意大利国旗色 */
  --italia-green: #009246;
  --italia-white: #f4f5f0;
  --italia-red: #ce2b37;

  /* 通用语义色 */
  --ok: #059669;
  --warn: #d97706;
  --danger: #dc2626;
  --info: #2563eb;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;

  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg: 0 10px 32px rgba(0,0,0,0.10), 0 4px 12px rgba(0,0,0,0.06);

  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --font-serif: "Georgia", "Times New Roman", "Songti SC", serif;
  --font-mono: "JetBrains Mono", "Fira Code", "Cascadia Code", Consolas, Monaco, monospace;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; }

body {
  font-family: var(--font-sans);
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.65;
  font-size: 15px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
}

/* ==================== CSS 意大利国旗图标 ==================== */
/* Windows 不支持国旗 emoji 彩色显示，用 CSS 绘制 */
.it-flag {
  display: inline-flex;
  width: 1.2em;
  height: 0.9em;
  border-radius: 2px;
  overflow: hidden;
  vertical-align: -0.1em;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.12);
  flex-shrink: 0;
}
.it-flag::before,
.it-flag::after {
  content: "";
  display: block;
  height: 100%;
}
.it-flag { background: var(--italia-white); }
.it-flag::before { width: 33.333%; background: var(--italia-green); }
.it-flag::after { width: 33.333%; background: var(--italia-red); margin-left: auto; }
/* 大号国旗 */
.it-flag-lg {
  width: 2.2em;
  height: 1.6em;
  border-radius: 4px;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.12), 0 2px 6px rgba(0,0,0,0.15);
}
.it-flag-xl {
  width: 3.5em;
  height: 2.6em;
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.18);
}

a { color: inherit; text-decoration: none; transition: color 0.2s; }
a:hover { color: var(--accent, var(--italia-green)); }

/* ==================== 顶部导航 ==================== */
.topbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 1px 0 rgba(0,0,0,0.02) inset, 0 2px 12px rgba(0,0,0,0.05);
}
.topbar-inner {
  max-width: 1600px;
  margin: 0 auto;
  padding: 10px 24px;
  display: flex;
  align-items: center;
  gap: 24px;
}
.topbar-home {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  flex-shrink: 0;
}
.tb-flag { font-size: 22px; }
.tb-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--accent, var(--italia-green));
}
.topbar-version-switch {
  display: flex;
  gap: 4px;
  margin-left: auto;
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-soft);
}
.version-switch-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);
  transition: all 0.2s;
  font-weight: 500;
}
.version-switch-btn:hover {
  color: var(--btn-accent, var(--text-primary));
  background: var(--bg-tertiary);
}
.version-switch-btn.active {
  color: var(--btn-accent);
  background: var(--bg-elevated);
  box-shadow: 0 0 0 1px var(--btn-accent), 0 0 16px var(--btn-glow);
}
.vsw-icon { font-size: 14px; }

.topbar-toc-toggle {
  display: none;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  align-items: center;
  gap: 6px;
}

/* ==================== 页面布局 ==================== */
.page-main {
  padding-top: 70px;
}
.main-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 24px 24px 60px;
}
.main-grid {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 32px;
  align-items: start;
}

/* ==================== 侧边目录 ==================== */
.toc-sidebar {
  position: sticky;
  top: 86px;
  max-height: calc(100vh - 110px);
  overflow-y: auto;
  padding: 20px 16px 20px 0;
  border-right: 1px solid var(--border-soft);
  font-size: 13px;
  scrollbar-width: thin;
  scrollbar-color: var(--border-color) transparent;
}
.toc-sidebar::-webkit-scrollbar { width: 6px; }
.toc-sidebar::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
.toc-title {
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 12px;
  font-weight: 600;
}
.toc-item {
  display: block;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  border-left: 2px solid transparent;
  margin-bottom: 2px;
  line-height: 1.45;
  transition: all 0.15s;
}
.toc-item:hover {
  color: var(--text-primary);
  background: var(--bg-secondary);
  border-left-color: var(--accent, var(--italia-green));
}
.toc-item.toc-level-1 {
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 10px;
}
.toc-item.toc-level-1:first-child { margin-top: 0; }
.toc-item.toc-level-2 {
  padding-left: 22px;
  font-size: 12.5px;
}
.toc-item.toc-level-3 {
  padding-left: 34px;
  font-size: 12px;
  color: var(--text-muted);
}
.toc-item.active {
  color: var(--accent, var(--italia-green));
  background: var(--accent-soft, rgba(0,146,70,0.1));
  border-left-color: var(--accent, var(--italia-green));
}

/* ==================== 主内容区 ==================== */
.main-grid > *:not(.toc-sidebar) {
  grid-column: 2;
  min-width: 0; /* allow content to shrink */
}

/* ==================== Hero ==================== */
.hero {
  position: relative;
  padding: 28px 28px;
  margin-bottom: 20px;
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-elevated) 100%);
  border: 1px solid var(--border-color);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}
.hero-bg-flag {
  position: absolute;
  top: 0; left: 0; bottom: 0;
  width: 6px;
  background: linear-gradient(180deg,
    var(--italia-green) 0%,
    var(--italia-green) 33.33%,
    var(--italia-white) 33.33%,
    var(--italia-white) 66.66%,
    var(--italia-red) 66.66%,
    var(--italia-red) 100%);
}
.hero::after {
  content: "";
  position: absolute;
  top: -50%; right: -20%;
  width: 60%; height: 200%;
  background: radial-gradient(ellipse at center, var(--accent-soft) 0%, transparent 60%);
  pointer-events: none;
}
.hero-content {
  position: relative;
  display: flex;
  gap: 24px;
  align-items: flex-start;
}
.hero-icon {
  font-size: 56px;
  line-height: 1;
  flex-shrink: 0;
  filter: drop-shadow(0 4px 20px var(--glow));
}
.hero-text { flex: 1; min-width: 0; }
.hero-eyebrow {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 11px;
}
.hero-version, .hero-level, .hero-time {
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
  letter-spacing: 0.08em;
  border: 1px solid var(--accent);
}
.hero-level, .hero-time {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-color: var(--border-color);
  font-weight: 500;
}
.hero-title {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 10px;
  letter-spacing: -0.01em;
}
.hero-version-tag {
  display: inline-block;
  padding: 2px 12px;
  background: var(--accent);
  color: #ffffff;
  border-radius: var(--radius-sm);
  font-size: 22px;
  font-weight: 700;
  margin-left: 6px;
  vertical-align: middle;
  box-shadow: 0 4px 16px var(--glow);
}
.hero-tagline {
  font-size: 17px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  font-style: italic;
}
.hero-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 16px;
  max-width: 720px;
}
.hero-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.hl-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  font-size: 12.5px;
  color: var(--text-secondary);
}
.hl-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 8px var(--glow);
}

/* ==================== 统计条 ==================== */
.stats-bar {
  display: flex;
  gap: 0;
  padding: 12px 20px;
  margin-bottom: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--accent);
}
.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 12px;
  border-right: 1px solid var(--border-soft);
}
.stat-item:last-child { border-right: none; }
.stat-num {
  font-size: 22px;
  font-weight: 700;
  color: var(--accent);
  line-height: 1.2;
}
.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* ==================== 标题 ==================== */
.section-title {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 26px;
  font-weight: 700;
  margin: 32px 0 14px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--border-color);
  position: relative;
}
.section-title::after {
  content: "";
  position: absolute;
  bottom: -2px; left: 0;
  width: 80px; height: 2px;
  background: var(--accent, var(--italia-green));
  box-shadow: 0 0 12px var(--glow);
}
.section-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px; height: 42px;
  border-radius: var(--radius-md);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 16px;
  font-weight: 700;
  border: 1px solid var(--accent);
  flex-shrink: 0;
}
.section-title-text { flex: 1; }

.subsection-title {
  font-size: 21px;
  font-weight: 600;
  margin: 24px 0 12px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}
.subsection-title::before {
  content: "";
  display: inline-block;
  width: 4px; height: 22px;
  background: var(--accent, var(--italia-green));
  border-radius: 2px;
  box-shadow: 0 0 8px var(--glow);
}

.subsubsection-title {
  font-size: 17px;
  font-weight: 600;
  margin: 16px 0 10px;
  color: var(--text-primary);
  padding-left: 12px;
  border-left: 3px solid var(--border-color);
}
.h4-title {
  font-size: 15px;
  font-weight: 600;
  margin: 12px 0 8px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ==================== 段落 ==================== */
.paragraph {
  margin: 8px 0;
  color: var(--text-secondary);
  line-height: 1.75;
}

/* ==================== 表格 ==================== */
.table-wrap {
  margin: 12px 0 16px;
  overflow-x: auto;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  scrollbar-width: thin;
  scrollbar-color: var(--border-color) transparent;
}
.table-wrap::-webkit-scrollbar { height: 6px; }
.table-wrap::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.data-table th {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-weight: 600;
  text-align: left;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
  position: sticky;
  top: 0;
  font-size: 13px;
  letter-spacing: 0.02em;
}
.data-table td {
  padding: 11px 14px;
  border-bottom: 1px solid var(--border-soft);
  color: var(--text-secondary);
  vertical-align: top;
}
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover {
  background: var(--bg-card-hover);
}
.data-table td.it-cell {
  color: var(--text-primary);
  font-weight: 500;
}

/* ==================== 意语可点击播放 ==================== */
.it-text {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  position: relative;
  padding: 2px 6px;
  margin: 0 -2px;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
  cursor: pointer;
}
.it-text:hover {
  background: var(--accent-soft, rgba(0,146,70,0.1));
}
.it-text.it-text-block {
  display: inline-block;
  width: 100%;
}
.it-word {
  color: var(--text-primary);
  font-style: italic;
  font-family: var(--font-serif);
  font-weight: 500;
}
.it-cell .it-word {
  font-style: normal;
  font-family: var(--font-sans);
}
.play-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px; height: 22px;
  border: none;
  background: transparent;
  color: var(--accent, var(--italia-green));
  font-size: 13px;
  cursor: pointer;
  border-radius: 50%;
  transition: all 0.2s;
  opacity: 0.7;
  padding: 0;
  flex-shrink: 0;
}
.it-text:hover .play-btn { opacity: 1; }
.play-btn:hover {
  background: var(--accent, var(--italia-green));
  color: #ffffff;
  transform: scale(1.1);
}
.play-btn.playing {
  background: var(--accent, var(--italia-green));
  color: #ffffff;
  opacity: 1;
  animation: pulse 1.2s ease-in-out infinite;
}
.play-btn-block {
  margin-left: 8px;
  width: 26px; height: 26px;
  font-size: 14px;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 var(--glow, rgba(0,146,70,0.5)); }
  50% { box-shadow: 0 0 0 8px transparent; }
}
.it-text.playing {
  background: var(--accent-soft, rgba(0,146,70,0.15));
  box-shadow: 0 0 0 1px var(--accent, var(--italia-green));
}

/* ==================== 引用块 ==================== */
.quote-block {
  margin: 12px 0 16px;
  padding: 14px 18px;
  background: var(--bg-card);
  border-left: 3px solid var(--text-muted);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.75;
}
.quote-block.quote-italian {
  border-left-color: var(--accent, var(--italia-green));
  background: linear-gradient(90deg, var(--accent-soft, rgba(0,146,70,0.08)) 0%, var(--bg-card) 100%);
}

/* ==================== 列表 ==================== */
.list-block {
  margin: 8px 0 14px;
  padding-left: 24px;
  color: var(--text-secondary);
}
.list-block li {
  margin: 4px 0;
  line-height: 1.7;
}
.list-block.list-ordered {
  list-style: decimal;
}
.list-block:not(.list-ordered) {
  list-style: none;
  padding-left: 0;
}
.list-block:not(.list-ordered) li {
  position: relative;
  padding-left: 22px;
}
.list-block:not(.list-ordered) li::before {
  content: "▸";
  position: absolute;
  left: 0;
  color: var(--accent, var(--italia-green));
  font-weight: 700;
}

/* ==================== 代码块 ==================== */
.code-block {
  margin: 12px 0 16px;
  padding: 16px 18px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre;
}
.inline-code {
  font-family: var(--font-mono);
  font-size: 0.88em;
  padding: 2px 6px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-soft);
  border-radius: 4px;
  color: var(--accent, var(--italia-green));
}

/* ==================== 分隔线 ==================== */
.divider {
  height: 1px;
  margin: 24px 0;
  background: linear-gradient(90deg, transparent, var(--border-color) 20%, var(--border-color) 80%, transparent);
  position: relative;
}
.divider::before {
  content: "";
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  background: var(--bg-primary);
  padding: 0 12px;
  width: 24px;
  height: 16px;
  border-radius: 3px;
  box-shadow: 0 0 0 1px var(--border-color);
  background:
    linear-gradient(to right,
      var(--italia-green) 0%, var(--italia-green) 33.33%,
      var(--italia-white) 33.33%, var(--italia-white) 66.66%,
      var(--italia-red) 66.66%, var(--italia-red) 100%);
}
}

/* ==================== 底部导航 ==================== */
.bottom-nav {
  max-width: 1600px;
  margin: 60px auto 0;
  padding: 28px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-top: 1px solid var(--border-color);
}
.bn-home {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-weight: 600;
  align-self: flex-start;
  transition: all 0.2s;
}
.bn-home:hover {
  background: var(--bg-elevated);
  border-color: var(--accent, var(--italia-green));
  color: var(--accent, var(--italia-green));
}
.bn-icon { font-size: 18px; }
.bn-others {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}
.bn-other {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  transition: all 0.25s;
  position: relative;
  overflow: hidden;
}
.bn-other::before {
  content: "";
  position: absolute;
  top: 0; left: 0; bottom: 0;
  width: 3px;
  background: var(--btn-accent, var(--italia-green));
  transform: scaleY(0);
  transform-origin: top;
  transition: transform 0.25s;
}
.bn-other:hover {
  background: var(--bg-elevated);
  border-color: var(--btn-accent, var(--italia-green));
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.bn-other:hover::before { transform: scaleY(1); }
.bno-icon { font-size: 24px; }
.bno-name {
  flex: 1;
  font-weight: 600;
  font-size: 15px;
}
.bno-arrow {
  color: var(--btn-accent, var(--italia-green));
  font-size: 18px;
  transition: transform 0.2s;
}
.bn-other:hover .bno-arrow { transform: translateX(4px); }

/* ==================== 返回顶部 ==================== */
.back-to-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 44px; height: 44px;
  border-radius: 50%;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  color: var(--accent, var(--italia-green));
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  visibility: hidden;
  transition: all 0.25s;
  z-index: 90;
  box-shadow: var(--shadow-md);
}
.back-to-top.visible {
  opacity: 1;
  visibility: visible;
}
.back-to-top:hover {
  background: var(--accent, var(--italia-green));
  color: #ffffff;
  transform: translateY(-3px);
  box-shadow: 0 8px 24px var(--glow, rgba(0,146,70,0.4));
}

/* ==================== 音频播放提示 ==================== */
.audio-player-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-elevated);
  border: 1px solid var(--accent, var(--italia-green));
  border-radius: 999px;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-primary);
  z-index: 100;
  box-shadow: 0 8px 32px var(--glow, rgba(0,146,70,0.4));
  transition: all 0.3s;
}
.audio-player-toast[hidden] {
  opacity: 0;
  pointer-events: none;
  transform: translateX(-50%) translateY(20px);
}
.toast-icon {
  font-size: 16px;
  animation: pulse 1.5s ease-in-out infinite;
}

/* ==================== 响应式 ==================== */
@media (max-width: 1024px) {
  .main-container {
    padding: 12px 14px 40px;
  }
  .main-grid {
    grid-template-columns: 1fr;
  }
  .toc-sidebar {
    position: fixed;
    top: 64px;
    left: 0;
    right: 0;
    bottom: 0;
    max-height: none;
    background: var(--bg-primary);
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    padding: 20px;
    z-index: 95;
    transform: translateX(-100%);
    transition: transform 0.3s;
    overflow-y: auto;
  }
  .toc-sidebar.open { transform: translateX(0); }
  .topbar-toc-toggle { display: inline-flex; }
  .topbar-version-switch { display: none; }
  .main-grid > *:not(.toc-sidebar) {
    grid-column: 1;
  }
}
@media (max-width: 720px) {
  .main-container { padding: 10px 12px 32px; }
  .topbar-inner { padding: 8px 14px; gap: 8px; }
  .tb-title { display: none; }
  .hero { padding: 20px 16px; margin-bottom: 14px; }
  .hero-content { flex-direction: column; gap: 8px; }
  .hero-icon { font-size: 36px; }
  .hero-title { font-size: 20px; }
  .hero-version-tag { font-size: 14px; padding: 2px 6px; }
  .stats-bar { flex-wrap: wrap; padding: 10px; margin-bottom: 16px; }
  .stat-item { min-width: 33.33%; border-right: none; }
  .section-title { font-size: 18px; gap: 8px; margin: 22px 0 10px; padding-bottom: 8px; }
  .section-number { width: 28px; height: 28px; font-size: 12px; }
  .subsection-title { font-size: 16px; margin: 16px 0 8px; }
  .subsubsection-title { font-size: 15px; margin: 12px 0 8px; }
  .h4-title { font-size: 14px; margin: 10px 0 6px; }
  .paragraph { margin: 6px 0; }
  .table-wrap { margin: 8px 0 12px; }
  .quote-block { margin: 8px 0 12px; padding: 12px 14px; }
  .list-block { margin: 6px 0 10px; }
  .list-block li { margin: 3px 0; }
  .code-block { margin: 8px 0 12px; padding: 12px 14px; font-size: 12px; }
  .divider { margin: 16px 0; }
  .data-table { font-size: 13px; }
  .data-table th, .data-table td { padding: 7px 8px; }
  .bottom-nav { padding: 16px 14px; gap: 10px; margin-top: 32px; }
  .bn-others { grid-template-columns: 1fr; gap: 8px; }
}
"""


def get_version_css(version: Dict[str, Any]) -> str:
    """返回各版本的特色 CSS（覆盖部分变量）。"""
    return f"""
:root {{
  --accent: {version["accent"]};
  --accent-soft: {version["accent_soft"]};
  --glow: {version["glow"]};
}}
body[data-version="{version["id"]}"] .hero-icon {{
  filter: drop-shadow(0 4px 24px {version["glow"]});
}}
body[data-version="{version["id"]}"] .hero-version-tag {{
  background: {version["accent"]};
  box-shadow: 0 0 32px {version["glow"]};
}}
/* 让特色色在元素上生效 */
body[data-version="{version["id"]}"] .section-title::after {{ background: {version["accent"]}; box-shadow: 0 0 12px {version["glow"]}; }}
body[data-version="{version["id"]}"] .subsection-title::before {{ background: {version["accent"]}; box-shadow: 0 0 8px {version["glow"]}; }}
body[data-version="{version["id"]}"] .stats-bar {{ border-left-color: {version["accent"]}; }}
body[data-version="{version["id"]}"] .stat-num {{ color: {version["accent"]}; }}
body[data-version="{version["id"]}"] .quote-block.quote-italian {{
  border-left-color: {version["accent"]};
  background: linear-gradient(90deg, {version["accent_soft"]} 0%, var(--bg-card) 100%);
}}
body[data-version="{version["id"]}"] .play-btn {{ color: {version["accent"]}; }}
body[data-version="{version["id"]}"] .play-btn:hover {{
  background: {version["accent"]};
  color: #ffffff;
}}
body[data-version="{version["id"]}"] .play-btn.playing {{
  background: {version["accent"]};
  color: #ffffff;
}}
body[data-version="{version["id"]}"] .it-text:hover {{ background: {version["accent_soft"]}; }}
body[data-version="{version["id"]}"] .it-text.playing {{
  background: {version["accent_soft"]};
  box-shadow: 0 0 0 1px {version["accent"]};
}}
body[data-version="{version["id"]}"] .toc-item:hover {{
  border-left-color: {version["accent"]};
}}
body[data-version="{version["id"]}"] .toc-item.active {{
  color: {version["accent"]};
  background: {version["accent_soft"]};
  border-left-color: {version["accent"]};
}}
body[data-version="{version["id"]}"] .section-number {{
  background: {version["accent_soft"]};
  color: {version["accent"]};
  border-color: {version["accent"]};
}}
body[data-version="{version["id"]}"] .list-block:not(.list-ordered) li::before {{
  color: {version["accent"]};
}}
body[data-version="{version["id"]}"] .back-to-top {{
  color: {version["accent"]};
  border-color: {version["accent"]};
}}
body[data-version="{version["id"]}"] .back-to-top:hover {{
  background: {version["accent"]};
  color: #ffffff;
  box-shadow: 0 8px 24px {version["glow"]};
}}
body[data-version="{version["id"]}"] .audio-player-toast {{
  border-color: {version["accent"]};
  box-shadow: 0 8px 32px {version["glow"]};
}}
body[data-version="{version["id"]}"] .inline-code {{ color: {version["accent"]}; }}
body[data-version="{version["id"]}"] .version-switch-btn.active {{
  color: {version["accent"]};
  box-shadow: 0 0 0 1px {version["accent"]}, 0 0 16px {version["glow"]};
}}
body[data-version="{version["id"]}"] .hl-dot {{
  background: {version["accent"]};
  box-shadow: 0 0 8px {version["glow"]};
}}
body[data-version="{version["id"]}"] .hero-version, body[data-version="{version["id"]}"] .hero-level, body[data-version="{version["id"]}"] .hero-time {{
  /* keep default */
}}
body[data-version="{version["id"]}"] .hero-version {{
  background: {version["accent_soft"]};
  color: {version["accent"]};
  border-color: {version["accent"]};
}}
"""


# ============================================================
# JavaScript
# ============================================================
COMMON_JS = r"""
(function() {
  "use strict";

  // ============ 音频播放管理 ============
  var audioCache = {};       // audio_id -> HTMLAudioElement
  var currentAudio = null;   // 当前正在播放的 audio
  var currentBtn = null;     // 当前正在播放的按钮

  function getAudioPath(id) {
    // audio/basic/basic_0001.mp3 等
    var version = document.body.dataset.version;
    return "audio/" + version + "/" + id + ".mp3";
  }

  function playAudio(id, btn) {
    // 如果当前正在播放同一个，暂停
    if (currentAudio && currentAudio.dataset.id === id) {
      currentAudio.pause();
      resetPlayingUI();
      return;
    }
    // 停止之前的
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    }
    resetPlayingUI();

    // 获取或创建 audio
    var audio = audioCache[id];
    if (!audio) {
      audio = new Audio(getAudioPath(id));
      audio.dataset.id = id;
      audioCache[id] = audio;
      audio.addEventListener("ended", function() {
        resetPlayingUI();
      });
      audio.addEventListener("error", function() {
        showToast("音频未生成：" + id, true);
        resetPlayingUI();
      });
    }
    // 重置时间
    audio.currentTime = 0;
    audio.play().then(function() {
      currentAudio = audio;
      currentBtn = btn;
      // 标记所有同 id 的元素为 playing
      document.querySelectorAll('[data-audio="' + id + '"]').forEach(function(el) {
        el.classList.add("playing");
      });
      document.querySelectorAll('.play-btn[data-audio="' + id + '"]').forEach(function(b) {
        b.classList.add("playing");
      });
      showToast("正在播放...");
    }).catch(function(err) {
      showToast("播放失败：" + (err.message || err), true);
    });
  }

  function resetPlayingUI() {
    document.querySelectorAll(".playing").forEach(function(el) {
      el.classList.remove("playing");
    });
    currentAudio = null;
    currentBtn = null;
    hideToast();
  }

  // ============ Toast 提示 ============
  var toastEl = document.getElementById("playerToast");
  var toastTimer = null;
  function showToast(msg, isError) {
    if (!toastEl) return;
    var textEl = toastEl.querySelector(".toast-text");
    if (textEl) textEl.textContent = msg;
    toastEl.hidden = false;
    if (isError) {
      toastEl.style.borderColor = "var(--danger)";
    } else {
      toastEl.style.borderColor = "";
    }
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(hideToast, 3000);
  }
  function hideToast() {
    if (toastEl) toastEl.hidden = true;
  }

  // ============ 绑定点击事件 ============
  document.addEventListener("click", function(e) {
    // 点击播放按钮
    var btn = e.target.closest(".play-btn");
    if (btn) {
      e.preventDefault();
      e.stopPropagation();
      var id = btn.dataset.audio;
      if (id) playAudio(id, btn);
      return;
    }
    // 点击 it-text 整体也触发播放
    var itText = e.target.closest(".it-text");
    if (itText) {
      var id2 = itText.dataset.audio;
      if (id2) {
        e.preventDefault();
        var btn2 = itText.querySelector(".play-btn");
        playAudio(id2, btn2 || itText);
      }
    }
  });

  // ============ 返回顶部 ============
  var backToTop = document.getElementById("backToTop");
  if (backToTop) {
    window.addEventListener("scroll", function() {
      if (window.scrollY > 400) {
        backToTop.classList.add("visible");
      } else {
        backToTop.classList.remove("visible");
      }
    });
    backToTop.addEventListener("click", function() {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // ============ 目录侧边栏（移动端） ============
  var tocToggle = document.getElementById("tocToggle");
  var tocSidebar = document.getElementById("tocSidebar");
  if (tocToggle && tocSidebar) {
    tocToggle.addEventListener("click", function() {
      tocSidebar.classList.toggle("open");
    });
    // 点击目录项后关闭（移动端）
    tocSidebar.querySelectorAll("a").forEach(function(a) {
      a.addEventListener("click", function() {
        if (window.innerWidth <= 1024) {
          tocSidebar.classList.remove("open");
        }
      });
    });
  }

  // ============ TOC 当前章节高亮 ============
  var tocItems = tocSidebar ? tocSidebar.querySelectorAll(".toc-item") : [];
  if (tocItems.length) {
    var sections = [];
    tocItems.forEach(function(item) {
      var href = item.getAttribute("href");
      if (href && href.startsWith("#")) {
        var target = document.getElementById(href.slice(1));
        if (target) sections.push({ el: target, link: item });
      }
    });
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          tocItems.forEach(function(i) { i.classList.remove("active"); });
          var match = sections.find(function(s) { return s.el === entry.target; });
          if (match) match.link.classList.add("active");
        }
      });
    }, { rootMargin: "-80px 0px -70% 0px", threshold: 0 });
    sections.forEach(function(s) { observer.observe(s.el); });
  }

  // ============ 键盘快捷键 ============
  document.addEventListener("keydown", function(e) {
    // ESC 关闭目录
    if (e.key === "Escape" && tocSidebar) {
      tocSidebar.classList.remove("open");
    }
    // 空格暂停/继续当前音频
    if (e.key === " " && e.target === document.body) {
      e.preventDefault();
      if (currentAudio) {
        if (currentAudio.paused) {
          currentAudio.play();
        } else {
          currentAudio.pause();
          resetPlayingUI();
        }
      }
    }
  });

})();
"""


# ============================================================
# 导航页（index.html）
# ============================================================
def build_index_html() -> str:
    """生成导航页。"""
    cards = []
    for v in VERSIONS:
        cards.append(f"""
    <a href="{v["id"]}.html" class="version-card" data-version="{v["id"]}"
       style="--accent: {v["accent"]}; --accent-soft: {v["accent_soft"]}; --glow: {v["glow"]};">
      <div class="vc-flag-stripe"></div>
      <div class="vc-body">
        <div class="vc-header">
          <div class="vc-icon">{v["icon"]}</div>
          <div class="vc-meta">
            <div class="vc-version">{v["name"]}</div>
            <div class="vc-version-it">{v["name_it"]}</div>
          </div>
          <div class="vc-level">{v["level"]}</div>
        </div>
        <h3 class="vc-tagline">{v["tagline"]}</h3>
        <p class="vc-desc">{v["description"]}</p>
        <div class="vc-highlights">
          {''.join(f"<span class='vc-hl'><span class='vc-hl-dot'></span>{h}</span>" for h in v["highlights"])}
        </div>
        <div class="vc-cta">
          <span>进入学习</span>
          <span class="vc-arrow">→</span>
        </div>
      </div>
    </a>
    """)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>设计留学作品集 · 意语词汇教程</title>
<meta name="description" content="赴意大利留学生设计作品集意语词汇教程 - 基础版 / 加强版 / 旗舰版三阶段进阶">
<style>{INDEX_CSS}</style>
</head>
<body>
  <div class="bg-gradient"></div>
  <div class="bg-flag"></div>

  <header class="index-header">
    <div class="ih-flag"><span class="it-flag it-flag-xl"></span></div>
    <h1 class="ih-title">设计留学作品集 · 意语词汇</h1>
    <p class="ih-subtitle">VOCABOLARIO DEL PORTFOLIO PER STUDIARE DESIGN IN ITALIA</p>
    <p class="ih-tagline">面向赴意大利留学生 · 三阶段进阶 · 意语点击即播</p>
  </header>

  <section class="intro-section">
    <div class="intro-grid">
      <div class="intro-card">
        <div class="intro-icon">🎯</div>
        <div class="intro-text">
          <h3>三阶段进阶</h3>
          <p>从基础开口到学术高阶，按 A1→C1 水平分层，找到最适合你的起点。</p>
        </div>
      </div>
      <div class="intro-card">
        <div class="intro-icon">🔊</div>
        <div class="intro-text">
          <h3>意语点击即播</h3>
          <p>所有意大利语片段均支持点击播放，跟读模仿，纠正发音，培养语感。</p>
        </div>
      </div>
      <div class="intro-card">
        <div class="intro-icon">💼</div>
        <div class="intro-text">
          <h3>场景化内容</h3>
          <p>覆盖面试、作品集介绍、设计评论、院校申请等真实场景，学完即可用。</p>
        </div>
      </div>
      <div class="intro-card">
        <div class="intro-icon">📅</div>
        <div class="intro-text">
          <h3>30天学习路径</h3>
          <p>每版配套 30 天冲刺计划，每天 15-30 分钟，系统化稳步提升。</p>
        </div>
      </div>
    </div>
  </section>

  <main class="cards-section">
    <h2 class="section-heading">选择你的起点</h2>
    <p class="section-sub">建议按顺序学习，但也可根据自身水平跳级</p>
    <div class="cards-grid">
      {''.join(cards)}
    </div>
  </main>

  <section class="path-section">
    <h2 class="section-heading">推荐学习路径</h2>
    <div class="path-flow">
      <div class="path-step" style="--accent: #10b981;">
        <div class="path-num">01</div>
        <div class="path-body">
          <div class="path-icon">🌱</div>
          <div class="path-name">基础版</div>
          <div class="path-detail">背熟核心词汇 + 万能句型 + 30 天养成开口习惯</div>
        </div>
      </div>
      <div class="path-arrow">→</div>
      <div class="path-step" style="--accent: #f59e0b;">
        <div class="path-num">02</div>
        <div class="path-body">
          <div class="path-icon">🚀</div>
          <div class="path-name">加强版</div>
          <div class="path-detail">分科词汇 + 面试问答 + 5 分钟作品集完整介绍</div>
        </div>
      </div>
      <div class="path-arrow">→</div>
      <div class="path-step" style="--accent: #a855f7;">
        <div class="path-num">03</div>
        <div class="path-body">
          <div class="path-icon">👑</div>
          <div class="path-name">旗舰版</div>
          <div class="path-detail">名校风格 + 设计大师 + 学术批评 + 高级语法</div>
        </div>
      </div>
    </div>
  </section>

  <section class="tips-section">
    <h2 class="section-heading">使用提示</h2>
    <div class="tips-grid">
      <div class="tip"><strong>🔊 播放：</strong>点击任意带喇叭图标的意大利语片段即可播放，再次点击暂停</div>
      <div class="tip"><strong>⌨️ 快捷键：</strong>按空格键可暂停/继续当前播放，按 ESC 关闭目录</div>
      <div class="tip"><strong>☰ 目录：</strong>左侧目录可快速跳转章节，移动端点击右上角按钮展开</div>
      <div class="tip"><strong>📱 跨设备：</strong>页面响应式设计，手机/平板/电脑均可流畅使用</div>
    </div>
  </section>

  <footer class="index-footer">
    <div class="footer-quote">
      <em>"Inizia con piccoli passi, ma inizia oggi."</em>
      <span class="quote-cn">— 从小步开始，但从今天开始。</span>
    </div>
    <div class="footer-info">
      <span><span class="it-flag"></span> In bocca al lupo! 🐺🍀</span>
      <span class="footer-sep">·</span>
      <span>设计留学作品集意语词汇教程</span>
    </div>
  </footer>
</body>
</html>
"""


INDEX_CSS = r"""
:root {
  /* 浅色主题 */
  --bg-primary: #f5f6f8;
  --bg-secondary: #ffffff;
  --bg-card: #ffffff;
  --bg-elevated: #f8f9fb;
  --text-primary: #1a1d2e;
  --text-secondary: #4a5170;
  --text-muted: #7a82a0;
  --border-color: #d8dce4;
  --italia-green: #009246;
  --italia-white: #f4f5f0;
  --italia-red: #ce2b37;
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --font-serif: "Georgia", "Times New Roman", "Songti SC", serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: var(--font-sans);
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.65;
  font-size: 15px;
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
  min-height: 100vh;
  position: relative;
}

/* CSS 意大利国旗图标（Windows 不支持国旗 emoji） */
.it-flag {
  display: inline-flex;
  width: 1.2em;
  height: 0.9em;
  border-radius: 2px;
  overflow: hidden;
  vertical-align: -0.1em;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.12);
  flex-shrink: 0;
  background: var(--italia-white);
}
.it-flag::before,
.it-flag::after {
  content: "";
  display: block;
  height: 100%;
}
.it-flag::before { width: 33.333%; background: var(--italia-green); }
.it-flag::after { width: 33.333%; background: var(--italia-red); margin-left: auto; }
.it-flag-xl {
  width: 3.5em;
  height: 2.6em;
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.18);
}

/* 背景 */
.bg-gradient {
  position: fixed;
  inset: 0;
  z-index: -2;
  background:
    radial-gradient(ellipse 60% 40% at 20% 0%, rgba(0, 146, 70, 0.10), transparent 60%),
    radial-gradient(ellipse 60% 40% at 50% 0%, rgba(244, 245, 240, 0.30), transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 0%, rgba(206, 43, 55, 0.10), transparent 60%),
    var(--bg-primary);
}
.bg-flag {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 4px;
  z-index: 50;
  background: linear-gradient(90deg,
    var(--italia-green) 0%, var(--italia-green) 33.33%,
    var(--italia-white) 33.33%, var(--italia-white) 66.66%,
    var(--italia-red) 66.66%, var(--italia-red) 100%);
  box-shadow: 0 0 24px rgba(0,0,0,0.3);
}

/* 头部 */
.index-header {
  max-width: 1100px;
  margin: 0 auto;
  padding: 100px 24px 60px;
  text-align: center;
}
.ih-flag {
  font-size: 80px;
  line-height: 1;
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  animation: float 4s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.ih-title {
  font-size: 44px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 12px;
  background: linear-gradient(135deg, var(--italia-green) 0%, var(--italia-red) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: shimmer 6s ease-in-out infinite;
}
@keyframes shimmer {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
.ih-subtitle {
  font-size: 13px;
  letter-spacing: 0.2em;
  color: var(--text-muted);
  margin-bottom: 8px;
  font-family: var(--font-serif);
  font-style: italic;
}
.ih-tagline {
  font-size: 15px;
  color: var(--text-secondary);
}

/* 介绍区 */
.intro-section {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px 24px 60px;
}
.intro-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.intro-card {
  display: flex;
  gap: 14px;
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  transition: all 0.25s;
}
.intro-card:hover {
  border-color: var(--italia-green);
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.3);
}
.intro-icon {
  font-size: 28px;
  flex-shrink: 0;
}
.intro-text h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.intro-text p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.55;
}

/* 主卡片区 */
.cards-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
}
.section-heading {
  text-align: center;
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 6px;
  letter-spacing: -0.01em;
}
.section-sub {
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
  margin-bottom: 32px;
}
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}
.version-card {
  position: relative;
  display: block;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 18px;
  overflow: hidden;
  transition: all 0.3s;
  color: var(--text-primary);
}
.version-card:hover {
  transform: translateY(-6px);
  border-color: var(--accent);
  box-shadow: 0 16px 48px var(--glow);
}
.vc-flag-stripe {
  height: 5px;
  background: linear-gradient(90deg,
    var(--italia-green) 0%, var(--italia-green) 33.33%,
    var(--italia-white) 33.33%, var(--italia-white) 66.66%,
    var(--italia-red) 66.66%, var(--italia-red) 100%);
}
.vc-body {
  padding: 28px 24px;
}
.vc-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}
.vc-icon {
  font-size: 48px;
  line-height: 1;
  filter: drop-shadow(0 4px 16px var(--glow));
}
.vc-meta {
  flex: 1;
}
.vc-version {
  font-size: 22px;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.02em;
}
.vc-version-it {
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-serif);
  font-style: italic;
  letter-spacing: 0.1em;
}
.vc-level {
  padding: 5px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--accent);
  color: var(--accent);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
}
.vc-tagline {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--text-primary);
}
.vc-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.7;
}
.vc-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 20px;
}
.vc-hl {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  background: var(--bg-elevated);
  border-radius: 999px;
  font-size: 12px;
  color: var(--text-secondary);
}
.vc-hl-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 6px var(--glow);
}
.vc-cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--accent);
  color: #ffffff;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
}
.version-card:hover .vc-cta {
  background: var(--text-primary);
}
.vc-arrow {
  transition: transform 0.2s;
}
.version-card:hover .vc-arrow {
  transform: translateX(6px);
}

/* 学习路径 */
.path-section {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 24px;
}
.path-flow {
  display: flex;
  align-items: stretch;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}
.path-step {
  flex: 1;
  min-width: 240px;
  max-width: 320px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-top: 3px solid var(--accent);
  border-radius: 14px;
  padding: 20px;
  position: relative;
  transition: all 0.25s;
}
.path-step:hover {
  transform: translateY(-3px);
  border-color: var(--accent);
  box-shadow: 0 12px 32px rgba(0,0,0,0.3);
}
.path-num {
  position: absolute;
  top: 14px; right: 16px;
  font-size: 32px;
  font-weight: 800;
  color: var(--accent);
  opacity: 0.25;
  letter-spacing: -0.05em;
}
.path-icon {
  font-size: 32px;
  margin-bottom: 8px;
}
.path-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 6px;
}
.path-detail {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.path-arrow {
  display: flex;
  align-items: center;
  font-size: 24px;
  color: var(--text-muted);
  font-weight: 300;
}

/* 提示区 */
.tips-section {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 24px;
}
.tips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}
.tip {
  padding: 14px 18px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-left: 3px solid var(--italia-green);
  border-radius: 8px;
  font-size: 13.5px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.tip strong {
  color: var(--text-primary);
  font-weight: 600;
}

/* 底部 */
.index-footer {
  max-width: 800px;
  margin: 60px auto 0;
  padding: 40px 24px 60px;
  text-align: center;
  border-top: 1px solid var(--border-color);
}
.footer-quote {
  margin-bottom: 20px;
  font-family: var(--font-serif);
}
.footer-quote em {
  display: block;
  font-size: 20px;
  color: var(--italia-green);
  margin-bottom: 6px;
  font-style: italic;
}
.quote-cn {
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-sans);
  font-style: normal;
}
.footer-info {
  font-size: 13px;
  color: var(--text-muted);
  display: flex;
  gap: 10px;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
}
.footer-sep { opacity: 0.5; }

@media (max-width: 720px) {
  .ih-flag { font-size: 56px; }
  .ih-title { font-size: 28px; }
  .ih-subtitle { font-size: 11px; }
  .index-header { padding: 70px 16px 40px; }
  .cards-section, .path-section, .tips-section, .intro-section { padding-left: 16px; padding-right: 16px; }
  .section-heading { font-size: 22px; }
  .vc-body { padding: 20px 16px; }
  .vc-icon { font-size: 36px; }
  .vc-version { font-size: 18px; }
  .vc-tagline { font-size: 16px; }
  .path-arrow { display: none; }
}
"""


# ============================================================
# 主流程
# ============================================================
def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    all_audio_items: List[Dict[str, str]] = []

    for version in VERSIONS:
        source_path = SOURCE_DIR / version["source"]
        if not source_path.exists():
            print(f"[!] 源文件不存在: {source_path}")
            continue

        md_text = source_path.read_text(encoding="utf-8")
        blocks = parse_markdown(md_text)

        collector = AudioCollector(version["id"])
        html_content = build_html(version, blocks, collector)

        output_path = WORK_DIR / f"{version['id']}.html"
        output_path.write_text(html_content, encoding="utf-8")
        print(f"[OK] 生成 {output_path.name}  | 意语片段: {len(collector.items)}")

        all_audio_items.extend(collector.items)

        # 保存该版本的音频清单
        list_path = WORK_DIR / f"audio_list_{version['id']}.json"
        list_path.write_text(
            json.dumps(
                {"version": version["id"], "items": collector.items},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    # 生成导航页
    index_html = build_index_html()
    index_path = WORK_DIR / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    print(f"[OK] 生成 {index_path.name}")

    # 保存全局音频清单
    global_list = WORK_DIR / "audio_list_all.json"
    global_list.write_text(
        json.dumps(all_audio_items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 总意语片段: {len(all_audio_items)}")
    print(f"[OK] 音频清单: {global_list}")


if __name__ == "__main__":
    main()
