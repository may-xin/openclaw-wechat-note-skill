"""
跨平台定时任务调度器
Linux/macOS → crontab
Windows      → schtasks
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

SYSTEM = platform.system()  # "Linux", "Darwin", "Windows"


# ── Linux / macOS ──────────────────────────────

def _crontab_list() -> str:
    try:
        r = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else ""
    except FileNotFoundError:
        return ""


def _crontab_write(content: str):
    try:
        p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=content)
        return p.returncode == 0
    except FileNotFoundError:
        return False


def _unix_add_job(schedule: str, command: str, label: str):
    """添加 crontab 任务，带标签去重"""
    current = _crontab_list()
    lines = [l for l in current.split("\n") if label not in l and l.strip()]
    lines.append(f"{schedule} {command}  # {label}")
    return _crontab_write("\n".join(lines) + "\n")


def _unix_remove_job(label: str):
    """移除带标签的 crontab 任务"""
    current = _crontab_list()
    lines = [l for l in current.split("\n") if label not in l]
    return _crontab_write("\n".join(lines) + "\n")


def _unix_has_job(label: str) -> bool:
    return label in _crontab_list()


# ── Windows ────────────────────────────────────

def _win_add_job(schedule: str, command: str, label: str):
    """Windows 任务计划程序"""
    # schtasks 分钟级调度用 /sc minute
    parts = schedule.split()
    minute = parts[0]
    hour = parts[1]

    if minute == "*" and hour == "*":
        # 每分钟
        schtask_cmd = [
            "schtasks", "/Create", "/F",
            "/TN", label,
            "/TR", command,
            "/SC", "MINUTE",
            "/MO", "1",
        ]
    elif minute != "*" and hour != "*":
        # 每天固定时间
        schtask_cmd = [
            "schtasks", "/Create", "/F",
            "/TN", label,
            "/TR", command,
            "/SC", "DAILY",
            "/ST", f"{hour.zfill(2)}:{minute.zfill(2)}",
        ]
    else:
        return False

    try:
        r = subprocess.run(schtask_cmd, capture_output=True, text=True)
        return r.returncode == 0
    except FileNotFoundError:
        return False


def _win_remove_job(label: str):
    try:
        subprocess.run(["schtasks", "/Delete", "/F", "/TN", label],
                       capture_output=True)
        return True
    except FileNotFoundError:
        return False


def _win_has_job(label: str) -> bool:
    try:
        r = subprocess.run(["schtasks", "/Query", "/TN", label],
                           capture_output=True, text=True)
        return r.returncode == 0
    except FileNotFoundError:
        return False


# ── 统一接口 ───────────────────────────────────

def add_job(schedule: str, command: str, label: str) -> bool:
    """
    添加定时任务
    schedule: cron 格式 "分 时 日 月 星期"
    command:  要执行的命令
    label:    任务标签（用于去重和删除）
    """
    if SYSTEM in ("Linux", "Darwin"):
        return _unix_add_job(schedule, command, label)
    else:
        return _win_add_job(schedule, command, label)


def remove_job(label: str) -> bool:
    """移除定时任务"""
    if SYSTEM in ("Linux", "Darwin"):
        return _unix_remove_job(label)
    else:
        return _win_remove_job(label)


def has_job(label: str) -> bool:
    """检查定时任务是否存在"""
    if SYSTEM in ("Linux", "Darwin"):
        return _unix_has_job(label)
    else:
        return _win_has_job(label)


def list_jobs(label_filter: str = "") -> list:
    """列出定时任务"""
    if SYSTEM in ("Linux", "Darwin"):
        lines = _crontab_list().split("\n")
        return [l for l in lines if label_filter in l and l.strip()]
    else:
        # Windows schtasks 不直接支持 label 过滤，返回全部
        return []


def get_system_label() -> str:
    """返回当前系统名称"""
    return SYSTEM
