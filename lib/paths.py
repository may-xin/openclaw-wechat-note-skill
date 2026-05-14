"""
跨平台路径解析
通过环境变量或 OpenClaw 配置自动定位工作目录
"""

import os
import json
import sys
from pathlib import Path


def _detect_openclaw_home() -> Path:
    """检测 OpenClaw 配置目录"""
    env = os.environ.get("OPENCLAW_HOME", "")
    if env:
        p = Path(env).expanduser()
        if (p / "openclaw.json").exists():
            return p
        # env 可能指向安装目录，检查其下的配置
        sub = p / ".openclaw"
        if (sub / "openclaw.json").exists():
            return sub

    # 默认路径（跨平台）：优先用户目录
    home = Path.home()
    candidates = [
        home / ".openclaw",
        home / ".config" / "openclaw",
        Path("/root/.openclaw"),
        Path("/opt/openclaw"),
    ]
    for c in candidates:
        if (c / "openclaw.json").exists():
            return c

    # 回退：env 或 home
    if env:
        return Path(env).expanduser()
    return home / ".openclaw"


def _detect_workspace() -> Path:
    """检测 workspace 路径
    优先: $OPENCLAW_HOME/.openclaw/workspace (安装目录下的 workspace)
    其次: openclaw.json 中配置的 workspace 字段
    回退: ~/.openclaw/workspace
    """
    # 1. OPENCLAW_HOME 环境变量下的 workspace
    env = os.environ.get("OPENCLAW_HOME", "")
    if env:
        p = Path(env).expanduser() / ".openclaw" / "workspace"
        if (p / "AGENTS.md").exists():
            return p

    # 2. openclaw.json 中配置的 workspace
    for config_dir in [OPENCLAW_HOME, Path.home() / ".openclaw", Path("/root/.openclaw")]:
        config_json = config_dir / "openclaw.json"
        if config_json.exists():
            try:
                with open(config_json) as f:
                    cfg = json.load(f)
                ws = cfg.get("workspace", "")
                if ws:
                    p = Path(ws).expanduser()
                    if p.exists():
                        return p
            except:
                pass

    # 3. 常见路径
    for p in [
        Path.home() / ".openclaw" / "workspace",
        Path("/opt/openclaw/.openclaw/workspace"),
        Path("/root/.openclaw/workspace"),
    ]:
        if (p / "AGENTS.md").exists():
            return p

    # 回退
    if env:
        return Path(env).expanduser() / ".openclaw" / "workspace"
    return Path.home() / ".openclaw" / "workspace"


OPENCLAW_HOME = _detect_openclaw_home()
WORKSPACE = _detect_workspace()
NOTES_DIR = WORKSPACE / "notes"
ILINK_DIR = WORKSPACE / "ilink-wechat"


def check_weixin_plugin() -> bool:
    """检查微信插件是否启用"""
    openclaw_json = OPENCLAW_HOME / "openclaw.json"
    if not openclaw_json.exists():
        return False
    try:
        with open(openclaw_json) as f:
            cfg = json.load(f)
        weixin = cfg.get("plugins", {}).get("entries", {}).get("openclaw-weixin", {})
        return weixin.get("enabled", False)
    except:
        return False


def get_accounts():
    """获取 Bot 账号列表"""
    accounts_json = OPENCLAW_HOME / "openclaw-weixin" / "accounts.json"
    if accounts_json.exists():
        try:
            with open(accounts_json) as f:
                return json.load(f)
        except:
            pass
    return []


def get_ilink_config():
    """获取 iLink 配置"""
    ilink_json = ILINK_DIR / "config.json"
    if ilink_json.exists():
        try:
            with open(ilink_json) as f:
                return json.load(f)
        except:
            pass
    return {}


# 预计算常用路径
CONCISE_FILE = NOTES_DIR / "NOTES.concise.md"
DETAILED_FILE = NOTES_DIR / "NOTES.detailed.md"
SENDER_SCRIPT = ILINK_DIR / "send.py"
STATE_FILE = NOTES_DIR / ".reminder_state.json"
