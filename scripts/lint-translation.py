#!/usr/bin/env python3
"""
翻译质量 lint 脚本。
翻完一个文件后、commit 之前跑一遍。有 FAIL 就不许提交。

用法: python3 scripts/lint-translation.py <file.md>
"""

import re
import sys
from pathlib import Path


def load_lines(path: str) -> list[str]:
    return Path(path).read_text(encoding="utf-8").splitlines()


def is_code_block_boundary(line: str) -> bool:
    return line.strip().startswith("```")


def classify_lines(lines: list[str]):
    """返回 (line_number, line_text, line_type) 列表。
    line_type: 'en' (> 引用块), 'cn' (中文散文), 'code', 'table', 'other'
    """
    result = []
    in_code = False
    for i, raw in enumerate(lines):
        s = raw.strip()
        if is_code_block_boundary(s):
            in_code = not in_code
            result.append((i + 1, raw, "code"))
            continue
        if in_code:
            result.append((i + 1, raw, "code"))
            continue
        if s.startswith(">"):
            result.append((i + 1, raw, "en"))
            continue
        if s.startswith("|"):
            result.append((i + 1, raw, "table"))
            continue
        if re.search(r"[一-鿿]", s):
            result.append((i + 1, raw, "cn"))
            continue
        result.append((i + 1, raw, "other"))
    return result


def find_architecture_section_range(lines: list[str]) -> tuple[int, int] | None:
    """返回 (start_line, end_line) 1-based，end_line 为第一个 --- 所在行。
    若未找到 ## 架构精读，返回 None（表示不限制）。
    """
    start = None
    for i, raw in enumerate(lines):
        s = raw.strip()
        if s == "## 架构精读":
            start = i + 1
        elif start is not None and s == "---":
            return (start, i + 1)
    return (start, len(lines)) if start else None


# ── 检查函数 ──────────────────────────────────────────────

FORBIDDEN_ENGLISH = [
    "ack", "dedupe", "dedup", "intent", "receipt", "preflight",
    "lane", "batch", "spawn", "render", "transport", "binding",
    "scope", "fail-closed", "fail.closed", "fail-open", "fail.open",
    "throttle", "stale", "durable", "preview", "draft", "live",
    "watchdog", "reconcile", "normalize", "handoff", "upstream",
    "downstream", "witness", "bootstrap", "teardown", "readiness",
    "inject", "observe", "timeline", "inventory", "backbone",
    "seam", "broker", "lease", "hook", "pool", "archive",
    "provision", "resume", "persist", "register", "claim",
    "cleanup", "fixture", "baseline", "candidate", "seed",
    # 2026-06-21 新增：架构精读英文混入治理
    "halt", "commit", "partial", "lockfile", "infrastructure", "severity",
    "chain", "negotiated", "hardening", "preload", "swap",
    "filesystem", "jail", "inode", "rollback", "uptime", "traversal",
    # 2026-06-21 第二批：高频未翻译词
    "proxy", "session", "token", "header", "client", "server", "caller",
    "message", "payload", "command", "flag", "mode", "profile", "policy",
    "endpoint", "route", "check", "downgrade", "auth", "tool", "channel",
    "bot", "host", "container", "exec", "sandbox", "backend", "frontend",
    "peer", "guild", "account", "owner", "operator", "admin", "binary",
    "path traversal", "zip bomb",
    # 2026-06-21 第三批：高频未翻译词
    "agent", "gateway", "shell", "plugin",
]

FORBIDDEN_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_ENGLISH) + r")\b",
    re.IGNORECASE,
)

TRANSLATION_ESE = [
    (r"通过.*进行", "通过...进行"),
    (r"对于.*来说", "对于...来说"),
    (r"使得", "使得"),
    (r"值得注意的是", "值得注意的是"),
    (r"在.*的情况下", "在...的情况下"),
    (r"进行\S+操作", "进行X操作"),
]

LABEL_PATTERNS = [
    r"\*\*英文原文\*\*",
    r"\*\*中文翻译\*\*",
    r"\*\*原文\*\*",
    r"\*\*译文\*\*",
]


def strip_inline_code(text: str) -> str:
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"\]\([^)]+\)", "]()", text)
    return text


def check_forbidden_english(classified, arch_range=None) -> list[str]:
    errors = []
    for lineno, text, ltype in classified:
        if ltype != "cn":
            continue
        if arch_range and not (arch_range[0] <= lineno <= arch_range[1]):
            continue
        clean = strip_inline_code(text)
        matches = FORBIDDEN_PATTERN.findall(clean)
        if matches:
            errors.append(
                f"  L{lineno} 禁止保留英文: {', '.join(set(m.lower() for m in matches))}"
            )
    return errors


def check_translation_ese(classified) -> list[str]:
    errors = []
    for lineno, text, ltype in classified:
        if ltype != "cn":
            continue
        for pattern, name in TRANSLATION_ESE:
            if re.search(pattern, text):
                errors.append(f"  L{lineno} 翻译腔「{name}」")
    return errors


def check_label_format(classified) -> list[str]:
    errors = []
    for lineno, text, ltype in classified:
        if ltype in ("code", "en"):
            continue
        for pat in LABEL_PATTERNS:
            if re.search(pat, text):
                errors.append(f"  L{lineno} 禁止标签格式: {text.strip()[:60]}")
    return errors


def check_long_sentences(classified) -> list[str]:
    errors = []
    for lineno, text, ltype in classified:
        if ltype != "cn":
            continue
        if text.strip().startswith("-") or text.strip().startswith("*"):
            continue
        clean = strip_inline_code(text)
        clean = re.sub(r"\*\*[^*]+\*\*", "", clean)
        sentences = re.split(r"[。？！]", clean)
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            cn_chars = len(re.findall(r"[一-鿿，：；、""’’（）]", sent))
            if cn_chars > 55:
                errors.append(
                    f"  L{lineno} single-sentence >50 cn chars ({cn_chars}): {sent[:60]}..."
                )
    return errors


def check_html_tags(classified) -> list[str]:
    errors = []
    for lineno, text, ltype in classified:
        if ltype in ("code", "en"):
            continue
        if re.search(r"<(?:details|summary|span|div|table|tr|td|th)\b", text, re.IGNORECASE):
            errors.append(f"  L{lineno} 禁止 HTML 标签: {text.strip()[:60]}")
    return errors


def check_missing_chinese_for_english(classified) -> list[str]:
    """检查是否每段英文 > 引用块后面跟着中文翻译"""
    errors = []
    i = 0
    items = classified
    while i < len(items):
        lineno, text, ltype = items[i]
        if ltype == "en":
            # 找到英文块的结束
            en_end = i
            while en_end < len(items) and items[en_end][2] == "en":
                en_end += 1
            # 跳过空行
            j = en_end
            while j < len(items) and items[j][1].strip() == "":
                j += 1
            # 检查后面是否有中文或代码块
            if j < len(items):
                next_type = items[j][2]
                if next_type not in ("cn", "code", "table", "other"):
                    # 下一段又是英文——可能漏翻
                    content = text.strip()[:60]
                    if not content.startswith("> ---") and not content.startswith("> ```"):
                        errors.append(
                            f"  L{lineno} 英文块后缺中文翻译: {content}"
                        )
            i = en_end
        else:
            i += 1
    return errors


def check_yongyou(classified) -> list[str]:
    """检查"拥有"滥用"""
    errors = []
    for lineno, text, ltype in classified:
        if ltype != "cn":
            continue
        if "拥有" in text:
            snippet = text.strip()[:60]
            errors.append(f"  L{lineno} 疑似拥有滥用(考虑用负责/管理/持有): {snippet}")
    return errors


# ── 主函数 ────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/lint-translation.py <file.md>")
        sys.exit(1)

    path = sys.argv[1]
    lines = load_lines(path)
    classified = classify_lines(lines)
    arch_range = find_architecture_section_range(lines)

    all_errors: dict[str, list[str]] = {}

    checks = [
        ("格式: 禁止标签前缀", check_label_format),
        ("格式: 禁止 HTML", check_html_tags),
        ("完整性: 英文块后缺翻译", check_missing_chinese_for_english),
        ("术语: 禁止保留英文", lambda c: check_forbidden_english(c, arch_range)),
        ("翻译腔: 欧化句式", check_translation_ese),
        ("可读性: 超长句(>70字)", check_long_sentences),
        ("术语: 拥有滥用", check_yongyou),
    ]

    total = 0
    for name, fn in checks:
        errs = fn(classified)
        if errs:
            all_errors[name] = errs
            total += len(errs)

    if total == 0:
        print(f"✅ PASS: {path} — 未发现问题")
        sys.exit(0)

    print(f"❌ FAIL: {path} — 发现 {total} 个问题\n")
    for category, errs in all_errors.items():
        print(f"[{category}] ({len(errs)})")
        for e in errs:
            print(e)
        print()

    sys.exit(1)


if __name__ == "__main__":
    main()
