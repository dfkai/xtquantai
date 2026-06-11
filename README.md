# xtquantai — 迅投 QMT 量化 AI 技能集

面向迅投 QMT / 投研终端的 **Agent Skills** 仓库：把量化策略开发的领域知识（因子回测、信号生成、实盘模板等）封装为标准 [SKILL.md](https://agentskills.io/specification) 技能，安装后可在 Claude Code、Cursor、Codex、Gemini CLI、Kimi Code 等 70+ AI 编程工具中直接使用。

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 本仓库曾是 xtquant 的 MCP 服务器实现，现已全面转型为 skill 仓库。旧 MCP 代码保留在 [`legacy-mcp`](https://github.com/dfkai/xtquantai/tree/legacy-mcp) 分支（tag `v0.1.0-mcp`），不再维护。

## 技能列表

| 技能 | 状态 | 说明 |
|------|------|------|
| [`qmt-inner-backtest`](skills/qmt-inner-backtest/SKILL.md) | ✅ 可用 | 根据策略描述 / 研报 PDF / 截图解读因子逻辑，基于母版脚本生成 QMT 内置日频截面因子回测策略（`after_init` 预计算信号 → `handlebar` 调仓执行，含 Barra 风格因子处理与防未来函数检查） |
| `qmt-future-trade` | 🚧 规划中 | 期货开平仓策略 |
| `qmt-live-strategy-template` | 🚧 规划中 | 目标持仓型实盘策略模板 |
| `qmt-live-signal-feishu` | 🚧 规划中 | 信号生成 + 飞书推送 |

欢迎提 issue / PR 补充新技能创意。

## 安装

### 方式一：npx skills（推荐，覆盖 70+ 工具）

```bash
# 交互式选择要安装到的工具
npx skills add dfkai/xtquantai

# 只装某个技能
npx skills add dfkai/xtquantai --skill qmt-inner-backtest

# 装到全局目录（所有项目可用）
npx skills add dfkai/xtquantai -g
```

### 方式二：Claude Code 原生插件

```text
/plugin marketplace add dfkai/xtquantai
/plugin install qmt-skills@xtquantai
```

### 方式三：Kimi Code CLI

```text
/plugins install https://github.com/dfkai/xtquantai
```

### 方式四：让你的 Agent 自己装

对任意 AI 编程工具说：

> 读取 https://raw.githubusercontent.com/dfkai/xtquantai/master/INSTALL.md 并按其中说明安装技能。

### 方式五：手动复制

把 `skills/<技能名>/` 整个文件夹复制到你所用工具的技能目录：

| 工具 | 项目级目录 | 用户级目录 |
|------|-----------|-----------|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Cursor (≥2.4) | `.cursor/skills/`（也读 `.agents/`、`.claude/`） | `~/.cursor/skills/` |
| OpenAI Codex CLI | `.agents/skills/` | `~/.agents/skills/` |
| GitHub Copilot | `.github/skills/`（也读 `.claude/`、`.agents/`） | — |
| Gemini CLI | `.gemini/skills/` 或 `.agents/skills/` | — |
| Kimi Code CLI | `.kimi-code/skills/` 或 `.agents/skills/` | — |
| Windsurf | `.windsurf/skills/` 或 `.agents/skills/` | — |
| OpenCode | `.opencode/skills/`、`.claude/skills/`、`.agents/skills/` | — |
| Cline (≥3.48) | `.cline/skills/` 或 `.claude/skills/`（需启用实验特性） | — |
| 字节 Trae | 仅 `.trae/skills/` | — |
| Qwen Code | 仅 `.qwen/skills/` | — |
| iFlow CLI | 仅 `.iflow/skills/` | — |

> 跨工具通用目录是 `.agents/skills/`；只用 Claude 系工具可以放 `.claude/skills/`。

## 使用示例

安装 `qmt-inner-backtest` 后，在你的 AI 工具中直接说：

> 这份研报（附 PDF/截图）的上下影线因子，帮我生成一个中证1000、Top 10 持仓、5 日调仓的 QMT 回测脚本。

Agent 会先输出策略规格表供你确认，再基于母版生成完整的 QMT 策略编辑器回测脚本，并提示你需要在 QMT 面板中手动核对的配置项。

⚠️ QMT / 投研终端仅支持 Windows，生成的策略脚本需在 Windows 上的 QMT 策略编辑器中运行；skill 本身（生成脚本的过程）不限平台。

## 仓库结构

```
xtquantai/
├── skills/                       # 技能目录（每个子目录一个 skill）
│   └── qmt-inner-backtest/
│       ├── SKILL.md              # 技能定义（agentskills.io 标准格式）
│       └── scripts/
│           └── daily-factors-backtest.py   # 回测母版脚本
├── .claude-plugin/
│   └── marketplace.json          # Claude Code 插件市场清单
├── kimi.plugin.json              # Kimi Code 插件清单
├── INSTALL.md                    # 给 agent 读的安装指令
└── docs/                         # 调研与设计文档
```

## 许可证

MIT — 详见 [LICENSE](LICENSE)。

## 致谢

- [迅投科技](https://www.thinktrader.net/) 提供的量化交易平台
- [Agent Skills](https://agentskills.io/) 开放技能标准
