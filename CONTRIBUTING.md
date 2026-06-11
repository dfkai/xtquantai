# 贡献指南

感谢你对 xtquantai 的关注！这是一个迅投 QMT 量化 AI 技能仓库，欢迎任何形式的参与。

## 参与方式

| 你想做什么 | 入口 |
|-----------|------|
| 提出新技能需求 / 想法 | [新技能需求 issue](https://github.com/dfkai/xtquantai/issues/new?template=skill-request.yml) |
| 反馈技能问题 | [Bug issue](https://github.com/dfkai/xtquantai/issues/new?template=bug-report.yml) |
| 使用咨询、量化思路交流 | [Discussions](https://github.com/dfkai/xtquantai/discussions) |
| 直接贡献技能或修复 | 提 Pull Request（见下文） |

提需求时不必客气：哪怕只有一句话的想法，也欢迎先开 issue 讨论可行性，再决定是否动手。

## 贡献一个技能

### 1. 目录结构

```
skills/<skill-name>/
├── SKILL.md           # 必需：技能定义
├── scripts/           # 可选：母版脚本、工具脚本
└── references/        # 可选：长文档拆分到这里
```

### 2. SKILL.md 规范

遵循 [Agent Skills 标准](https://agentskills.io/specification)：

- frontmatter 只用 `name` + `description` 两个字段；`name` 必须与目录名完全一致（小写字母、数字、连字符）
- `description` 写清楚**何时触发**：用户提到什么关键词、什么场景该用这个技能
- 正文控制在 500 行 / 5000 tokens 以内，超出部分拆到 `references/`
- 所有路径用相对路径，禁止硬编码本机路径或某个工具的专属目录
- 不使用工具私有字段（如 `allowed-tools`、`whenToUse`、`paths`），保证跨工具可用

### 3. 内容质量要求（量化领域特有）

- **防未来函数**：涉及信号生成的，必须有时序说明（如 `shift(1)`），并在自检清单中体现
- **容错优先**：QMT 数据接口可能返回空/None，脚本须能容错而非崩溃
- **不静默编造参数**：研报参数缺失时，技能应指导 agent 标注假设并请用户确认
- **声明验证环境**：母版脚本请注明在哪个 QMT 版本下跑通过

### 4. 提交前校验

```bash
npx skills-ref validate skills/<skill-name>
```

CI 会对所有技能自动跑同样的校验，校验不过的 PR 无法合并。

### 5. 提交 PR

1. Fork 并从 `master` 拉分支
2. 完成改动，更新 README 技能列表
3. 按 PR 模板填写自检清单
4. 提交后请留意 CI 结果和评审意见

## 评审标准

维护者评审时主要看：

1. 技能定位是否清晰（与现有技能不重复、触发条件明确）
2. 是否符合上面的结构与质量规范
3. 生成的脚本是否能在 QMT 中实际运行（可能请你提供验证截图/日志）

一般 1~3 天内会有首次回应。

## 行为准则

参与本项目即表示你同意遵守 [行为准则](CODE_OF_CONDUCT.md)。简单说：友善、就事论事、尊重不同水平的参与者。
