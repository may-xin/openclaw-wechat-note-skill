# OpenClaw WeChat Notes Skill

## 概述

OpenClaw WeChat Notes 为 OpenClaw 提供一套完整的微信集成笔记系统，跨平台支持 Linux / macOS / Windows。

**架构原则：大模型仅处理用户主动发起的笔记查询和添加。推送、提醒、清理均由 Python 脚本独立执行。**

---

## 一、自我介绍

首次调用时输出：

```
📋 OpenClaw WeChat Notes v1.2

  • 记笔记 — 说「记一下 xxx」
  • 定时提醒 — 说「提醒我 15:30 开会」
  • 每日摘要 — 默认 10:00 推送（可自定义）
  • 看笔记 — 说「notes」/「详细 notes」
  • 自动清理 — 30 天前笔记静默清除
```

---

## 二、笔记类型

### 普通笔记（不带时间）
- `记一下 xxx` → 写入精简版 `- xxx` + 详细版含时间戳
- 会在每日摘要中推送

### 定时提醒（带时间）
- `提醒我 15:30 开会`
- `明天 9:00 提交报告`
- `每周一 10:00 周会`
- 写入详细版含 `reminder:` 元数据，到点 cron 自动推送

---

## 三、重复检测

写入前对比精简版已有条目：
- 精确重复 → 告知跳过，不写入
- 疑似重复 → 询问是否保留
- 无重复 → 直接写入

---

## 四、交互流程

### 添加笔记时
```
用户说「记一下 xxx」
  → 重复检测
  → 写入 concise + detailed
  → 调用 check_daily.py
  → 已配置: 「📅 已设置每天 10:00 推送」
  → 未配置: 「📅 还没有设置每日摘要，是否添加？（回复时间 或 暂不提醒）」
```

### 查看笔记时
```
用户说「notes」
  → 读取 concise.md
  → 发送笔记内容
  → 调用 check_daily.py（同上）
```

### 用户回复时间
```
用户说「设置 9:00」
  → 更新 cron 为 9:00
  → 回复「✅ 已设置每天 9:00 推送」
```

### 用户回复暂不提醒
```
用户说「暂不提醒」
  → 写入 .daily_snooze.json，7 天内不问
  → 回复「⏭️ 7 天内不再提醒」
```

---

## 五、自动调度（不经过 LLM）

| cron | 脚本 | 功能 |
|------|------|------|
| 每天 10:00 | `send_daily.py` | 推送笔记摘要（区分普通/定时） |
| 每分钟 | `reminder_checker.py` | 检查到期提醒并推送 |
| 每天 0:00 | `cleanup_notes.py` | 静默清除 30 天前笔记 |

---

## 六、存储格式

### 精简版 `NOTES.concise.md`
```markdown
# 📝 木星的笔记（简洁版）
> 最后更新：2026-05-14 17:15

## 2026-05-14
- Telegram 加交易群
- ⏰ 15:30 开会
```

### 详细版 `NOTES.detailed.md`
```markdown
## 2026-05-14
- **Telegram 加交易群**
  备注内容
  添加时间：2026-05-14 13:19

- **提醒：开会**
  时间：15:30
  reminder: 2026-05-14T15:30:00
  repeat: none
  done: false
```

---

## 七、文件结构

```
workspace/
├── openclaw-wechat-skill/    # 技能定义 + 公共库
│   ├── SKILL.md
│   ├── configure.py
│   └── lib/{paths,scheduler}.py
├── notes/                    # 笔记存储 + 执行脚本
│   ├── NOTES.concise.md
│   ├── NOTES.detailed.md
│   ├── send_daily.py         # 每日摘要
│   ├── reminder_checker.py   # 定时提醒
│   ├── cleanup_notes.py      # 自动清理
│   └── check_daily.py        # 摘要状态检查
└── ilink-wechat/             # iLink 发送
    └── send.py
```

---

## 八、大模型边界

| 功能 | 执行方 | 经 LLM |
|------|--------|--------|
| 添加笔记 | LLM | ✅ |
| 查询笔记 | LLM | ✅ |
| 重复检测 | LLM | ✅ |
| 配置交互 | LLM | ✅ |
| 每日摘要 | cron → Python | ❌ |
| 定时提醒 | cron → Python | ❌ |
| 自动清理 | cron → Python | ❌ |
| 摘要状态检查 | Python（LLM 调用） | ❌ |
