# OpenClaw WeChat Notes Skill

## 概述

跨平台微信集成笔记系统（Linux / macOS / Windows）。

**核心原则：LLM 只处理笔记查询和添加。推送、清理、状态检查均由 Python 脚本执行。**

---

## 一、自我介绍

首次调用时：

```
📋 OpenClaw WeChat Notes v1.2

  • 记笔记 — 说「记一下 xxx」
  • 定时提醒 — 说「提醒我 15:30 开会」
  • 每日摘要 — 默认 10:00 推送
  • 看笔记 — 说「notes」/「详细 notes」
  • 自动清理 — 30 天前静默清除
```

---

## 二、笔记类型

**普通笔记（不带时间）**：`记一下 xxx` → 每日摘要推送

**定时提醒（带时间）**：`提醒我 15:30 开会` → 到点推送，支持重复（每天/每周/每月）

---

## 三、重复检测

- 精确重复 → 跳过
- 疑似重复 → 询问
- 无重复 → 写入

---

## 四、交互流程

每次用户发消息时，**先调用脚本再处理请求**：

```
用户发消息
  ├─ check_reminders.py  → 有到期提醒？推送
  ├─ 处理用户请求（记笔记/查笔记/...）
  └─ check_daily.py      → 未配置摘要？提示用户
```

### 记笔记
```
「记一下 xxx」
  → 重复检测 → 写入 concise + detailed
  → 「📅 每天 10:00 推送」（已配置）
  → 「📅 还没有设置每日摘要，是否添加？」（未配置）
```

### 查笔记
```
「notes」        → 发精简版
「详细 notes」   → 发详细版
```

### 设置/暂不提醒
```
「设置 9:00」    → 更新 cron，回复「✅ 已设置」
「暂不提醒」     → 7 天免打扰
```

---

## 五、自动调度

| cron | 脚本 | 经 LLM |
|------|------|--------|
| 每天 10:00 | `send_daily.py` | ❌ |
| 每天 0:00 | `cleanup_notes.py` | ❌ |

定时提醒不靠 cron 轮询，用户交互时 `check_reminders.py` 顺带检查。

---

## 六、存储格式

**精简版 `NOTES.concise.md`：**
```markdown
- Telegram 加交易群
- ⏰ 15:30 开会
```

**详细版 `NOTES.detailed.md`：**
```markdown
- **提醒：开会**
  时间：15:30
  reminder: 2026-05-14T15:30:00
  repeat: none
  done: false
```

---

## 七、文件结构

```
notes/
├── NOTES.concise.md         # 精简版
├── NOTES.detailed.md        # 详细版
├── send_daily.py            # 每日摘要（cron）
├── check_reminders.py       # 提醒检查（交互时）
├── check_daily.py           # 摘要状态（交互时）
└── cleanup_notes.py         # 自动清理（cron）

openclaw-wechat-skill/
├── SKILL.md                 # 本文件
├── configure.py             # 配置向导
└── lib/{paths,scheduler}.py
```
