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

## 二、笔记类型（严格区分）

### 📝 普通笔记
- `记一下 xxx` → 写入笔记区
- **仅出现在每日摘要推送中**
- 不会被定时触发

### ⏰ 定时提醒
- `提醒我 15:30 开会` → 写入提醒区，含 `reminder:` 时间戳
- **仅由 `check_reminders.py` 到点触发推送**
- **不出现在每日摘要中**（避免重复推送）
- 支持重复：每天/每周/每月

---

## 三、重复检测

- 精确重复 → 跳过
- 疑似重复 → 询问
- 无重复 → 写入

---

## 四、交互流程

### 定时提醒（优先处理）

规则：
1. 仅回复「收到 👌」，不附加任何其他文字
2. 写入文件在后台完成，不向用户展示
3. 不触发重复检测、摘要检查
4. 无主题时默认标题为「提醒」

```
用户：「提醒我 15:30 开会」
  → 回复: 收到 👌
  → 后台: 写入 concise + detailed

用户：「2分钟后提醒我」  ← 无主题
  → 回复: 收到 👌
  → 后台: 标题用「提醒」
```

### 每次交互时（自动）
```
用户发任何消息
  → 处理用户请求
  → check_daily.py → 显示摘要状态（仅笔记相关时）
```

### 记笔记
```
「记一下 xxx」
  → 重复检测 → 写入
  → check_daily.py → 显示摘要状态
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
| 每分钟 | `check_reminders.py` | ❌ |
| 每天 0:00 | `cleanup_notes.py` | ❌ |

---

## 六、存储格式

**笔记区** → 每日摘要用  |  **提醒区** → 定时触发用

两份文件各自分两段：

### 精简版 `NOTES.concise.md`
```markdown
# 📝 笔记
- Telegram 加交易群

---

# ⏰ 定时提醒
- ⏰ 15:30 开会
```

### 详细版 `NOTES.detailed.md`
```markdown
## 📝 笔记
- **Telegram 加交易群**  添加时间：2026-05-14 13:19

## ⏰ 定时提醒
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
