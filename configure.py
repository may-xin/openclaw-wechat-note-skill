#!/usr/bin/env python3
"""
OpenClaw WeChat Notes — 配置向导（跨平台版）
用法: python configure.py        # 交互式配置
      python configure.py --check  # 非交互检查
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from paths import (
    OPENCLAW_HOME, WORKSPACE, NOTES_DIR, ILINK_DIR,
    check_weixin_plugin, get_accounts, get_ilink_config,
)
from scheduler import add_job, remove_job, has_job, get_system_label

GREEN = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"; RESET = "\033[0m"
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)

ok = lambda m: print(f"{GREEN}✅{RESET} {m}")
err = lambda m: print(f"{RED}❌{RESET} {m}")
warn = lambda m: print(f"{YELLOW}⚠️{RESET} {m}")

PYTHON = sys.executable


def safe_input(prompt, default=""):
    """安全获取用户输入，非 TTY 回退"""
    try:
        return input(prompt).strip()
    except (EOFError, OSError):
        print(default)
        return default


def step1_plugin():
    print("\n📡 [1/4] 检查 Clawbot 插件...")
    print(f"    系统: {get_system_label()}")
    print(f"    OpenClaw 目录: {OPENCLAW_HOME}")
    print(f"    Workspace: {WORKSPACE}")
    if check_weixin_plugin():
        ok("Weixin 插件已启用")
        return True
    err("Weixin 插件未启用")
    print(f"    配置文件: {OPENCLAW_HOME / 'openclaw.json'}")
    return False


def step2_ilink():
    print("\n🔗 [2/4] iLink 配置...")
    cfg = get_ilink_config()
    token = cfg.get("token", "")
    to_user = cfg.get("to_user", "")
    if token and to_user and len(token) > 20:
        ok(f"iLink 就绪 → {to_user[:25]}...")
        return True
    accounts = get_accounts()
    if accounts:
        warn(f"检测到 Bot 账号: {accounts[0]}")
        warn("需要完整 token ({account_id}@im.bot:{secret})")
        print(f"    配置文件: {ILINK_DIR / 'config.json'}")
    else:
        err("未找到 Bot 账号")
    return False


def step3_daily(interactive=True):
    print("\n📅 [3/4] 每日摘要...")
    if has_job("openclaw-notes-daily"):
        ok("每日摘要已配置")
        return True, None
    if not interactive:
        warn("每日摘要未配置")
        return False, None
    print("    是否启用每日定时推送？")
    choice = safe_input("    时间 (如 9:00) / 跳过 > ", "跳过")
    if choice.lower() in ("跳过", "no", "n", "skip", ""):
        print("    ⏭️ 已跳过")
        return True, None
    try:
        h, m = map(int, choice.replace("：", ":").split(":"))
        schedule = f"{m} {h} * * *"
        cmd = f"{PYTHON} {NOTES_DIR / 'send_daily.py'}"
        if add_job(schedule, cmd, "openclaw-notes-daily"):
            time_str = f"{h:02d}:{m:02d}"
            ok(f"每日 {time_str} 推送已设置")
            return True, time_str
        err("调度任务添加失败")
        return False, None
    except Exception:
        err("时间格式错误（示例: 9:00）")
        return False, None


def step4_reminder(interactive=True):
    print("\n🔔 [4/4] 定时提醒...")
    if has_job("openclaw-notes-reminder"):
        ok("定时提醒已启用（每分钟检查）")
        return True
    if not interactive:
        warn("定时提醒未配置")
        return False
    print("    是否启用定时提醒？（每分钟检查一次）")
    choice = safe_input("    是/否 > ", "否")
    if choice.lower() in ("否", "no", "n", "skip", "不", ""):
        print("    ⏭️ 已跳过")
        return True
    cmd = f"{PYTHON} {NOTES_DIR / 'reminder_checker.py'}"
    if add_job("* * * * *", cmd, "openclaw-notes-reminder"):
        ok("定时提醒已启用")
        return True
    err("调度任务添加失败")
    return False


def main():
    parser = argparse.ArgumentParser(description="OpenClaw WeChat Notes 配置向导")
    parser.add_argument("--check", action="store_true", help="仅检查，不交互")
    args = parser.parse_args()

    print("=" * 50)
    print("  OpenClaw WeChat Notes — 配置向导")
    print(f"  平台: {get_system_label()}")
    if args.check:
        print("  模式: 仅检查（非交互）")
    print("=" * 50)

    interactive = not args.check
    r1 = step1_plugin()
    r2 = step2_ilink()
    r3, daily_time = step3_daily(interactive)
    r4 = step4_reminder(interactive)

    print("\n" + "=" * 50)
    print("  配置状态")
    print("=" * 50)
    results = [
        ("Clawbot 插件", r1),
        ("iLink 通道", r2),
        ("每日摘要", r3),
        ("定时提醒", r4),
    ]
    for name, val in results:
        print(f"  {'✅' if val else '❌'} {name}")

    if all(v for _, v in results):
        print(f"\n{GREEN}✅ 全部就绪{RESET}")
        if daily_time:
            print(f"    每日摘要：{daily_time}")
        print(f"    笔记目录：{NOTES_DIR}")
        print(f"    iLink 目录：{ILINK_DIR}")
    else:
        print(f"\n{YELLOW}⚠️  部分未完成，请检查上述 ❌ 项{RESET}")


if __name__ == "__main__":
    main()
