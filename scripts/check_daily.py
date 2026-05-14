#!/usr/bin/env python3
"""
每日摘要状态检查 — LLM 交互时调用，不经过调度器
返回 JSON：是否已配置 + 配置的时间
"""

import json
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir.parent / "openclaw-wechat-skill" / "lib"))

from scheduler import has_job, list_jobs


def check():
    """检查每日摘要配置状态，返回 JSON"""
    if has_job("openclaw-notes-daily"):
        jobs = list_jobs("openclaw-notes-daily")
        time_str = "10:00"
        for line in jobs:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    h = int(parts[1])
                    m = int(parts[0])
                    time_str = f"{h:02d}:{m:02d}"
                except:
                    pass
        return {
            "configured": True,
            "time": time_str,
            "message": f"📅 已设置每日 {time_str} 推送笔记摘要"
        }
    else:
        return {
            "configured": False,
            "time": None,
            "message": "📅 还没有设置每日摘要。是否添加？（回复时间如 9:00，或「暂不提醒」）"
        }


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, ensure_ascii=False))
