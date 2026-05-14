#!/usr/bin/env python3
"""
提醒检查器 — 用户交互时调用
扫描 detailed.md 中 ⏰ 区域的到期提醒并推送
窗口：5 分钟内，未标记 done 的触发
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

script_dir = Path(__file__).resolve().parent
DETAILED_FILE = script_dir / "NOTES.detailed.md"
STATE_FILE = script_dir / ".reminder_state.json"

# 找 ilink 发送器
sender = script_dir.parent / "ilink-wechat" / "send.py"
if not sender.exists():
    sender = Path.home() / ".openclaw" / "workspace" / "ilink-wechat" / "send.py"


def parse_reminders():
    if not DETAILED_FILE.exists():
        return []

    content = DETAILED_FILE.read_text(encoding="utf-8")
    reminders = []

    # 只解析 ⏰ 区域的内容
    sections = content.split("## ⏰")
    if len(sections) < 2:
        return []
    reminder_section = sections[1]

    pattern = re.compile(
        r'^\s*[-*]\s+\*\*(提醒：.+?)\*\*\s*\n'
        r'(.*?)'
        r'reminder:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
        re.MULTILINE | re.DOTALL
    )

    for match in pattern.finditer(reminder_section):
        title = match.group(1).strip()
        block = match.group(2)
        reminder_str = match.group(3).strip()

        if "done: true" in block:
            continue

        try:
            rt = datetime.fromisoformat(reminder_str)
        except ValueError:
            continue

        repeat = "none"
        rm = re.search(r'repeat:\s*(\S+)', block)
        if rm:
            repeat = rm.group(1)

        reminders.append({
            "title": title,
            "reminder_time": rt,
            "reminder_str": reminder_str,
            "repeat": repeat,
        })

    return reminders


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {"sent": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def mark_done(reminder_str):
    content = DETAILED_FILE.read_text(encoding="utf-8")
    idx = content.find(reminder_str)
    if idx < 0:
        return
    line_end = content.find("\n", idx)
    if line_end < 0:
        line_end = len(content)
    new_content = content[:line_end + 1] + "done: true\n" + content[line_end + 1:]
    DETAILED_FILE.write_text(new_content, encoding="utf-8")


def update_repeat(reminder_str, repeat):
    content = DETAILED_FILE.read_text(encoding="utf-8")
    old_time = datetime.fromisoformat(reminder_str)
    if repeat == "daily":
        new_time = old_time + timedelta(days=1)
    elif repeat.startswith("weekly"):
        new_time = old_time + timedelta(days=7)
    elif repeat == "monthly":
        new_time = old_time + timedelta(days=30)
    else:
        return
    new_str = new_time.strftime("%Y-%m-%dT%H:%M:%S")
    content = content.replace(f"reminder: {reminder_str}", f"reminder: {new_str}")
    content = content.replace(f"reminder: {new_str}\ndone: true", f"reminder: {new_str}")
    DETAILED_FILE.write_text(content, encoding="utf-8")


def send_reminder(title, reminder_time):
    time_str = reminder_time.strftime("%H:%M")
    msg = f"⏰ {title}\n  时间：{time_str}"

    for python in ("python3", "python"):
        try:
            r = subprocess.run(
                [python, str(sender), msg],
                capture_output=True, text=True, timeout=15
            )
            if r.returncode == 0:
                return True
        except Exception:
            continue
    return False


def main():
    now = datetime.now()
    reminders = parse_reminders()
    state = load_state()

    for r in reminders:
        diff = (now - r["reminder_time"]).total_seconds()
        # 窗口：已到期且未超过 5 分钟
        if diff < 0 or diff > 300:
            continue

        key = f"{r['title']}_{r['reminder_str']}"
        if key in state["sent"]:
            continue

        print(f"[reminder] 触发: {r['title']}", flush=True)
        if send_reminder(r["title"], r["reminder_time"]):
            state["sent"].append(key)
            save_state(state)

            if r["repeat"] != "none":
                update_repeat(r["reminder_str"], r["repeat"])
            else:
                mark_done(r["reminder_str"])

    # 清理 1 小时前的状态
    cutoff = (now - timedelta(hours=1)).isoformat()
    state["sent"] = [k for k in state["sent"] if not k.startswith(cutoff[:13])]
    save_state(state)


if __name__ == "__main__":
    main()
