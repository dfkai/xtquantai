# 跨工具 Skill 仓库调研结论（2026-06-11）

> 由 30 个调研 agent 完成，每条关键结论均经一手来源（官方文档/changelog/仓库）对抗性核查。
> 原始数据：`research-raw-2026-06-11.json`。本文档是给仓库改造工作直接用的行动依据。

## 1. 核心结论

**SKILL.md（Agent Skills）已是跨工具事实标准，"一份 skill 全工具可用"完全成立。**

- 规范：https://agentskills.io/specification （Anthropic 2025-10-16 首发，2025-12-18 开放为标准）
- frontmatter 必填仅 `name` + `description`；`name` 必须与父目录名一致（小写字母/数字/连字符）
- 正文建议 <500 行 / <5000 tokens，长内容拆 `references/`，脚本放 `scripts/`，相对路径引用
- 校验：`skills-ref validate ./my-skill`（github.com/agentskills/agentskills）
- 跨工具 skill 只依赖 `name`/`description` + 正文 + 脚本；**不要用** `allowed-tools`（Claude 实验字段）、`whenToUse`（Kimi 专有）、`paths`（Cursor 专有）等扩展字段

## 2. 工具兼容性矩阵（2026-06 实测验证）

| 工具 | 支持 SKILL.md | 读取目录（项目级） | 备注 |
|------|--------------|------------------|------|
| Claude Code | ✅ | `.claude/skills/` | 用户级 `~/.claude/skills/`；plugin 机制见 §4 |
| Cursor (≥2.4) | ✅ | `.cursor/skills/`、`.agents/skills/`、兼容 `.claude/skills/`、`.codex/skills/` | 全局 `~/.cursor/skills/` 等；monorepo 嵌套目录也扫 |
| OpenAI Codex CLI | ✅ | `.agents/skills/` | 用户级 `~/.agents/skills/`；**不读 .claude/skills** |
| GitHub Copilot | ✅ | `.github/skills/`、`.claude/skills/`、`.agents/skills/` | `gh skill install`（2026-04 起） |
| Gemini CLI | ✅ | `.gemini/skills/`、`.agents/skills/`（优先） | `gemini skills install`；**不读 .claude/skills** |
| Kimi Code CLI | ✅ | `.kimi-code/skills/`、`.agents/skills/` | 新一代产品（旧 kimi-cli 停维护）；`/import-from-cc-codex` 可导入 Claude 配置；plugin 机制见 §4 |
| Windsurf | ✅ | `.windsurf/skills/`、`.agents/skills/` | 开启 Claude 配置读取后也扫 `.claude/skills/` |
| OpenCode | ✅ | `.opencode/skills/` → `.claude/skills/` → `.agents/skills/` | 顺序搜索 |
| Cline (≥3.48) | ✅ | `.cline/skills/`、`.claude/skills/` | 实验特性需手动启用 |
| 字节 Trae | ✅ | 仅 `.trae/skills/` | 需 symlink/复制适配 |
| Qwen Code | ✅ | 仅 `.qwen/skills/` | `.agents/skills` 支持是 open issue (#2042) |
| iFlow CLI | ✅ | 仅 `.iflow/skills/` | 需 symlink/复制适配 |
| Roo Code | ⚠️ | — | 已于 2026-05-15 关停 |

要点：`.agents/skills/` 是跨工具互操作目录（Codex/Cursor/Gemini/Copilot/Windsurf/OpenCode/Kimi 七家直读）；`.claude/skills/` 覆盖 Claude Code/Cursor/Copilot/Cline/OpenCode。

## 3. 仓库布局（推荐方案）

本仓库是**分发仓库**（用户从这里装 skill，而非把仓库当工作目录），所以顶层用 `skills/` 布局（`npx skills` 和 anthropics/skills 官方仓库的标准）：

```
xtquantai/
├── skills/
│   ├── qmt-inner-backtest/
│   │   ├── SKILL.md              # 标准格式，工具中立
│   │   └── scripts/daily-factors-backtest.py
│   ├── qmt-future-trade/         # 计划中
│   ├── qmt-live-strategy-template/
│   └── qmt-live-signal-feishu/
├── .claude-plugin/
│   └── marketplace.json          # → Claude Code /plugin 安装
├── kimi.plugin.json              # → Kimi /plugins install 安装
├── README.md                     # 技能总表 + 按工具分段安装说明（抄 addyosmani/agent-skills）
├── INSTALL.md                    # 给 agent 读的安装指令（抄 obra/superpowers 模式）
└── docs/                         # 本调研等
```

- `marketplace.json` 最小示例：`{"name":"xtquantai","owner":{"name":"dfkai"},"plugins":[{"name":"qmt-skills","source":"./","description":"..."}]}`（发布前 `claude plugin validate .`）
- `kimi.plugin.json`：`{"name":"xtquantai","version":"0.1.0","skills":"./skills/"}`（name 须匹配 `[a-z0-9][a-z0-9_-]{0,63}`）

## 4. 用户安装方式（写进 README 的内容）

```bash
# 通用（70+ 工具，Claude Code/Cursor/Codex/Gemini/Copilot/OpenCode/Windsurf...）
npx skills add dfkai/xtquantai                 # 交互选工具
npx skills add dfkai/xtquantai --skill qmt-inner-backtest   # 装单个
npx skills add dfkai/xtquantai -g              # 装到全局目录
```

```text
# Claude Code 原生
/plugin marketplace add dfkai/xtquantai
/plugin install qmt-skills@xtquantai

# Kimi Code CLI
/plugins install https://github.com/dfkai/xtquantai

# 手动兜底（所有工具）
把 skills/<name>/ 整个文件夹复制到对应目录（见 §2 矩阵）
```

## 5. 发布渠道

| 渠道 | 方式 | 成本 |
|------|------|------|
| **skills.sh**（Vercel 官方目录站） | **零提交**：用户 `npx skills add` 后靠安装遥测自动上榜，且自动生成落地页 `skills.sh/dfkai/xtquantai/<skill>` | 0 |
| Claude plugin 社区市场 | platform.claude.com/plugins/submit 提交，过审进 anthropics/claude-plugins-community | 一次提交 |
| VoltAgent/awesome-agent-skills | 24.9k★ 的 curated 索引，提 PR 求曝光 | 一次 PR |

**关于"做一个带 install.md 的网页"**：skills.sh 会自动为每个 skill 生成带安装命令的落地页，头部仓库（anthropics/skills 149k★、obra/superpowers 223k★、addyosmani/agent-skills 52k★）都没有自建安装网页——主流做法是 README 即安装文档 + skills.sh 落地页 + 一份给 agent 读的 raw INSTALL.md（用户对自己的 agent 说"去读 https://raw.githubusercontent.com/dfkai/xtquantai/main/INSTALL.md 并照做"）。自建网页（GitHub Pages）可作为后期增强，范例参考 aitmpl.com（davila7/claude-code-templates）。

## 6. 待办（改造执行清单）

1. [ ] 旧 MCP 代码打 tag/留 legacy 分支，清空 master
2. [ ] `skills/qmt-inner-backtest/` 入库（已暂存在 `skills/`），修两处：
   - SKILL.md 第 17 行 `.cursor/skills/...` 硬编码路径 → 改相对路径 `scripts/daily-factors-backtest.py`
   - 文中引用的三个尚不存在的 skill（qmt-future-trade 等）→ 保留作规划或暂删
3. [ ] `skills-ref validate` 跑一遍校验
4. [ ] 写 README（技能表 + 按工具安装段）、INSTALL.md（agent 可读）
5. [ ] 加 `.claude-plugin/marketplace.json` + `claude plugin validate .`
6. [ ] 加 `kimi.plugin.json`
7. [ ] 发布后：提 PR 到 VoltAgent/awesome-agent-skills；视情况提交 Claude 社区市场

## 7. 勘误记录（核查中发现的两处常见误传）

- Claude plugin 钉版本：git URL 末尾 `#ref`（如 `...git#v1.0.0`），**不是** `@ref`；`@` 仅用于 `插件名@marketplace名`
- Kimi Code CLI 的 npm 安装要求 Node.js ≥22.19.0（≥24.15.0 是源码构建要求）；curl 安装脚本不依赖 Node
