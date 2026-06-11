# INSTALL.md — Agent 安装指令

> 本文件写给 AI 编程助手（agent）阅读。如果用户让你"安装 dfkai/xtquantai 的技能"，请按以下步骤执行。

## 步骤

1. **获取技能文件**。任选其一：
   - `git clone --depth 1 https://github.com/dfkai/xtquantai.git /tmp/xtquantai`
   - 或逐个下载 raw 文件：`https://raw.githubusercontent.com/dfkai/xtquantai/master/skills/<skill-name>/...`

2. **确定目标目录**。根据你当前运行所在的工具，选择技能目录（优先项目级；用户要求全局安装时用用户级）：

   | 你是 | 项目级目标目录 |
   |------|---------------|
   | Claude Code | `.claude/skills/` |
   | Cursor | `.cursor/skills/` 或 `.agents/skills/` |
   | OpenAI Codex CLI | `.agents/skills/` |
   | GitHub Copilot | `.github/skills/` |
   | Gemini CLI | `.gemini/skills/` 或 `.agents/skills/` |
   | Kimi Code CLI | `.kimi-code/skills/` 或 `.agents/skills/` |
   | Windsurf | `.windsurf/skills/` 或 `.agents/skills/` |
   | OpenCode | `.opencode/skills/` |
   | Cline | `.cline/skills/` |
   | 字节 Trae | `.trae/skills/` |
   | Qwen Code | `.qwen/skills/` |
   | iFlow CLI | `.iflow/skills/` |
   | 其他/不确定 | `.agents/skills/` |

3. **复制技能**。把仓库中 `skills/` 下用户想要的技能目录**整个**复制过去（必须包含 `SKILL.md` 和 `scripts/` 等全部内容），保持目录名不变：

   ```bash
   mkdir -p <目标目录>
   cp -r /tmp/xtquantai/skills/qmt-inner-backtest <目标目录>/
   ```

   用户未指定技能时，默认安装全部可用技能（当前为 `qmt-inner-backtest`）。

4. **验证**。确认 `<目标目录>/<skill-name>/SKILL.md` 存在，且 frontmatter 中 `name` 与目录名一致。

5. **告知用户**：安装了哪些技能、装到了哪个目录、可能需要重启工具或新开会话才能加载。

## 可用技能

| 名称 | 用途 |
|------|------|
| `qmt-inner-backtest` | 解读策略描述/研报，生成迅投 QMT 内置日频因子回测脚本 |

## 注意

- 不要修改 SKILL.md 内容或目录结构。
- 技能内脚本以相对路径互相引用，拆开复制会损坏技能。
- QMT 生成的策略脚本需在 Windows 的 QMT 策略编辑器中运行，但安装技能本身不限平台。
