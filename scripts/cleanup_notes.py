#!/usr/bin/env python3
"""
笔记自动清理 — 每天凌晨执行，删除 30 天前的条目，静默无通知
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

script_dir = Path(__file__).resolve().parent
CONCISE = script_dir / "NOTES.concise.md"
DETAILED = script_dir / "NOTES.detailed.md"
KEEP_DAYS = 30


def clean_concise():
    """清理精简版：删除 30 天前的条目，保留无日期的（视为当天）"""
    if not CONCISE.exists():
        return

    content = CONCISE.read_text(encoding="utf-8")
    lines = content.split("\n")
    cutoff = datetime.now() - timedelta(days=KEEP_DAYS)

    new_lines = []
    current_date = None

    for line in lines:
        # 检测日期标题
        date_match = re.match(r'^## (\d{4}-\d{2}-\d{2})', line)
        if date_match:
            try:
                current_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            except:
                current_date = None
            new_lines.append(line)
            continue

        # 非笔记行直接保留
        if not line.strip().startswith("-"):
            new_lines.append(line)
            continue

        # 带日期的条目，超期则跳过
        if current_date and current_date < cutoff:
            continue

        new_lines.append(line)

    CONCISE.write_text("\n".join(new_lines), encoding="utf-8")


def clean_detailed():
    """清理详细版：删除 30 天前的条目"""
    if not DETAILED.exists():
        return

    content = DETAILED.read_text(encoding="utf-8")
    cutoff = datetime.now() - timedelta(days=KEEP_DAYS)

    # 按日期段分割
    sections = re.split(r'(## \d{4}-\d{2}-\d{2}.*(?:\n|$))', content)
    new_content = []

    for i, section in enumerate(sections):
        # 日期标题
        date_match = re.match(r'## (\d{4}-\d{2}-\d{2})', section)
        if date_match:
            try:
                section_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                if section_date < cutoff:
                    # 跳过这个日期段
                    continue
            except:
                pass
        new_content.append(section)

    DETAILED.write_text("".join(new_content), encoding="utf-8")


def main():
    clean_concise()
    clean_detailed()


if __name__ == "__main__":
    main()
