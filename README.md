# OpenClaw WeChat Notes Skill

跨平台微信集成笔记系统，支持 **Linux / macOS / Windows**。

## 功能

- 📝 **记笔记** — 同时保存精简版和详细版
- 👀 **查笔记** — 默认发精简版，可随时查看详细版
- 📅 **每日摘要** — 自定义时间自动推送到微信
- ⏰ **定时提醒** — 支持一次性/重复提醒，到点自动推送

## 架构

```
大模型（LLM）    → 笔记查询 / 笔记添加（用户主动触发）
cron / schtasks  → 每日摘要 / 定时提醒（独立执行，不经 LLM）
iLink API        → 微信消息推送（直连，不经过 LLM）
```

## 快速开始

```bash
# 1. 配置检查
python configure.py --check

# 2. 交互式配置
python configure.py

# 3. 使用
# 跟 OpenClaw 说「记一下 xxx」→ 保存笔记
# 说「提醒我 15:30 开会」→ 设置定时提醒
# 说「notes」→ 查看笔记
```

## 项目结构

```
openclaw-wechat-skill/
├── SKILL.md              # 技能定义
├── configure.py          # 跨平台配置向导
└── lib/
    ├── paths.py          # 跨平台路径解析
    └── scheduler.py      # crontab / schtasks 调度器
```

## 依赖

- Python 3.7+（标准库，零外部依赖）
- OpenClaw Weixin 插件
- iLink WeChat 发送模块

## 平台支持

| 功能 | Linux | macOS | Windows |
|------|-------|-------|---------|
| 笔记管理 | ✅ | ✅ | ✅ |
| 每日推送 | crontab | crontab | schtasks |
| 定时提醒 | crontab | crontab | schtasks |
| 路径检测 | 自动 | 自动 | 自动 |
