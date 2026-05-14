# OpenClaw WeChat Notes Skill

## 概述

OpenClaw WeChat Notes（以下简称「本技能」）为 OpenClaw 提供一套完整的微信集成笔记系统，**跨平台支持 Linux / macOS / Windows**。

**架构原则：大模型仅处理用户主动发起的笔记查询和笔记添加。每日摘要推送、定时提醒触发均由调度器 + Python 脚本独立执行，不经过大模型。**

**跨平台适配：**
- Linux / macOS → crontab
- Windows → schtasks（任务计划程序）
- 所有脚本均为纯 Python，无需 shell 依赖

---

## 一、首次使用：自我介绍

当用户首次调用本技能时（关键词：`note`、`notes`、`笔记`、`记一下`、`记住`），输出以下介绍：

```
📋 OpenClaw WeChat Notes v1.1

我能帮你：
  • 记笔记 — 说「记一下 xxx」保存精简版+详细版
  • 看笔记 — 说「notes」发精简版，「详细 notes」发完整版
  • 每日摘要 — 自定义时间，自动推送精简版笔记到微信
  • 定时提醒 — 说「提醒我 15:30 开会」到期自动推送

功能说明：
  • 笔记查询/添加 → 经过大模型处理
  • 定时推送/提醒 → 纯脚本执行，不消耗 AI token
```

---

## 二、笔记记录规则

### 普通笔记
- `记一下 xxx` / `记个笔记` / `note` / `remember`

### 重复检测
写入前对比精简版已有条目：
- 关键词重叠 ≥ 50% → 疑似重复
- 向用户发送：`⚠️ 已有相似笔记「{已有条目}」，保留新笔记吗？（是/否）`
- 用户选「是」→ 追加；选「否」→ 丢弃
- 精确重复（文本 ≥ 80% 相同）→ 直接告知 `已存在相同笔记，跳过`

### 定时提醒笔记
支持以下自然语言格式：
- `提醒我 15:30 开会`
- `记一下 明天 9:00 提交报告`
- `提醒 18:00 买东西` / `18:00 提醒我 xxx`
- `每周一 10:00 周会`（支持重复提醒）

**解析规则：**
- 提取时间（HH:MM 或 明天 HH:MM 或 日期 HH:MM）
- 提取提醒内容
- 重复模式关键词：`每天`、`每周一/二/三/四/五/六/日`、`每月x号`

### 存储规则
1. 同时更新两个文件（按日期分组）：
   - **精简版** `notes/NOTES.concise.md` — 每条一行：
     - 普通笔记：`- 内容`
     - 定时提醒：`- ⏰ {时间} 内容`
   - **详细版** `notes/NOTES.detailed.md` — 完整上下文，含时间戳 + 提醒元数据（reminder 字段）

2. 定时提醒在详细版中额外记录：
   ```markdown
   - **提醒：开会**  
     时间：2026-05-14 15:30  
     reminder: 2026-05-14T15:30:00  
     repeat: none
   ```

3. 每次修改更新文件顶部的「最后更新」时间戳

### 文件路径
```
workspace/
├── openclaw-wechat-skill/   # 技能定义 + 公共库
│   ├── SKILL.md
│   ├── configure.py          # 跨平台配置向导
│   └── lib/
│       ├── paths.py          # 跨平台路径解析
│       └── scheduler.py      # 跨平台调度器 (cron/schtasks)
├── notes/                    # 笔记存储 + 执行脚本
│   ├── NOTES.concise.md
│   ├── NOTES.detailed.md
│   ├── send_daily.py         # 每日摘要（Python，跨平台）
│   └── reminder_checker.py   # 定时提醒（Python，跨平台）
└── ilink-wechat/             # iLink 发送模块
    └── send.py
```

---

## 三、笔记查看规则

| 用户输入 | 响应 |
|---------|------|
| `notes` / `看笔记` / `有什么笔记` | 发送精简版内容 |
| `详细 notes` / `完整笔记` / `看详细的` | 发送详细版内容 |

精简版作为消息正文发送；详细版内容较长时发送文件。

---

## 四、配置流程

当用户首次使用笔记功能、或说「配置 notes」/「设置笔记」时执行：

### 步骤 1：检查 Weixin 插件

读取 `/root/.openclaw/openclaw.json` → `plugins.entries.openclaw-weixin.enabled`

- ❌ **未启用**：
  ```
  ⚠️ 检测到 OpenClaw Weixin 插件未启用。

  请先在 OpenClaw 中配置微信 Clawbot 插件：
  1. 打开 OpenClaw 控制台 → 插件 → openclaw-weixin
  2. 启用并完成 Bot 注册
  3. 完成后回复「已配置」
  ```
- ✅ **已启用** → 步骤 2

### 步骤 2：同步 iLink 配置

检查 `workspace/ilink-wechat/config.json` 的 token 和 to_user 字段。有效则跳过，缺失则提示用户提供。

### 步骤 3：每日摘要设置

询问用户：
```
📅 每日笔记摘要设置

是否需要每天定时推送精简版笔记？

A. 需要（请回复时间，如 9:00 / 12:00 / 21:00）
B. 不需要（回复「跳过」）
```

**用户选择时间** → 更新 crontab 中的 `send_daily.sh` 执行时间为用户指定时间（转换为 UTC）

### 步骤 4：启用定时提醒

```
⏰ 是否启用定时提醒功能？
  • 你可以在笔记中添加提醒时间，到期自动推送
  • 需要每分钟检查一次，资源消耗极低
  • 回复「是」或「不」
```

- **同意** → 添加 crontab `* * * * * ... reminder_checker.py`（每分钟执行）
- **拒绝** → 跳过

### 步骤 5：完成

```
✅ OpenClaw WeChat Notes 配置完成

  • 笔记存储：本地文件系统
  • iLink 通道：已连接
  • 每日摘要：{时间 或 未启用}
  • 定时提醒：{已启用 或 未启用}
  • 使用方式：说「记一下 xxx」或「提醒我 15:30 xxx」
```

### 未配置每日摘要时的提醒
- 由 `daily_reminder.py` 脚本执行（cron，不经 LLM）
- 每天 10:00 检查一次
- 若未配置 → 发微信：`📅 您还没有设置每日摘要。是否添加？回复「设置 9:00」或「暂不提醒」`
- 用户回复「暂不提醒」→ 7 天内不再提醒（记录在 `.daily_reminder_state.json`）
- 用户回复时间 → 自动配置 cron

---

## 五、每日摘要机制

**实现：** 调度器 → `send_daily.py` → 读取精简版 → iLink 发送

**推送逻辑：**
1. 读取精简版笔记，提取条目
2. 若无普通笔记，不发送
3. 格式化发送

**未配置提醒：** `daily_reminder.py` 每天 10:00 检查，未配置则推送提醒（7 天内不重复）

---

## 六、定时提醒机制

**实现：** 调度器每分钟执行 `reminder_checker.py`（Linux/macOS → crontab，Windows → schtasks），**不经过大模型**。

**检查逻辑：**
1. 解析 `NOTES.detailed.md`，提取带 `reminder:` 字段的条目
2. 比对 `reminder` 时间与当前时间（±30 秒容差）
3. 匹配则通过 iLink 发送提醒
4. 已触发的提醒标记 `done: true`
5. 重复提醒（daily/weekly/monthly）自动计算下次提醒时间

**提醒格式：**
```
⏰ 提醒：开会
  设置时间：15:30
```

---

## 七、大模型边界

| 功能 | 执行方式 | 经过 LLM |
|------|---------|----------|
| 添加普通笔记 | LLM 解析 → 写入文件 | ✅ |
| 添加定时提醒 | LLM 解析 → 写入文件（含 reminder 元数据） | ✅ |
| 查询笔记 | LLM 读取文件 → 回复 | ✅ |
| 配置向导 | LLM 交互式引导 | ✅ |
| 每日摘要推送 | 调度器 → Python | ❌ |
| 未配置摘要提醒 | 调度器 → Python | ❌ |
| 定时提醒触发 | cron → python | ❌ |
| iLink 消息发送 | python 直调 API | ❌ |

---

## 八、依赖

- `workspace/ilink-wechat/` — iLink 微信发送模块
- Python 3.7+（标准库，零外部依赖）
- OpenClaw Weixin 插件（需启用）
- 系统调度器：Linux/macOS → crontab ｜ Windows → 任务计划程序

---

## 九、维护

- 笔记文件为 Markdown，可直接编辑
- Linux/macOS: `crontab -l` 查看定时任务
- Windows: `schtasks /Query` 查看定时任务
- `python configure.py` 重新运行配置向导（跨平台）
