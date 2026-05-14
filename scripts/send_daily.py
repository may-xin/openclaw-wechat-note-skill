#!/usr/bin/env python3
"""
每日笔记摘要发送器
只推送普通笔记，定时提醒独立触发，不重复推送
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "openclaw-wechat-skill" / "lib"))
try:
    from paths import CONCISE_FILE, SENDER_SCRIPT
except ImportError:
    notes_dir = Path(__file__).resolve().parent
    CONCISE_FILE = notes_dir / "NOTES.concise.md"
    SENDER_SCRIPT = notes_dir.parent / "ilink-wechat" / "send.py"


def main():
    if not CONCISE_FILE.exists():
        return

    content = CONCISE_FILE.read_text(encoding="utf-8")
    date_str = datetime.now().strftime("%m/%d")

    normal = []
    timed_count = 0

    for line in content.split("\n"):
        line = line.strip()
        if not line.startswith("- "):
            continue
        if "⏰" in line:
            timed_count += 1
        else:
            normal.append(line)

    # 没有任何笔记
    if not normal and timed_count == 0:
        return

    # 只推送普通笔记，定时提醒由 check_reminders.py 独立触发
    if not normal:
        return  # 只有定时提醒，不推送

    msg = f"📝 笔记 ({date_str})\n" + "\n".join(normal)

    if timed_count > 0:
        msg += f"\n\n另有 {timed_count} 条定时提醒，到点自动推送"

    for python in ("python3", "python"):
        try:
            r = subprocess.run(
                [python, str(SENDER_SCRIPT), msg],
                capture_output=True, text=True, timeout=20
            )
            if r.returncode == 0:
                print(f"[daily] {r.stdout.strip()}", flush=True)
                return
        except Exception:
            continue


if __name__ == "__main__":
    main()
