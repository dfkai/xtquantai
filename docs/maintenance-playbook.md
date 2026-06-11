# 维护手册（maintainer playbook）

> 给仓库维护者（及协助维护的 AI agent）的日常运营指南。社区可见，规则透明。

## 分工

- **维护者（dfkai）**：产出技能（核心能力）、对策略逻辑做最终把关
- **AI agent**：issue 分诊、标签管理、PR 初审（结构/规范/CI）、文档维护、发布操作

## 标签体系

| 标签 | 用途 |
|------|------|
| `skill-request` | 新技能需求（issue 模板自动打） |
| `bug` | 技能/脚本问题（issue 模板自动打） |
| `enhancement` | 现有技能改进 |
| `documentation` | 文档相关 |
| `question` | 使用咨询（适合引导去 Discussions） |
| `good first issue` | 适合新人上手 |
| `help wanted` | 欢迎社区认领 |
| `planned` | 已纳入路线图的技能 |
| `wontfix` | 不做，附原因 |

## Issue 分诊流程（建议每周 1~2 次）

1. 新 issue 24~72h 内首次回应（哪怕只是「收到，周末细看」）
2. 打标签；信息不全的，引导按模板补充
3. `skill-request` 的处理路径：
   - 值得做 → 打 `planned`，回复预期排期，纳入 README 规划表
   - 想法不错但暂不做 → 留 issue 开放，打 `help wanted` 欢迎社区贡献
   - 不适合 → 礼貌说明原因后打 `wontfix` 并关闭
4. `question` 类引导到 Discussions，沉淀为可搜索的问答

## PR 评审流程

1. CI 必须全绿（skills-ref 校验、目录名一致性、manifest JSON 合法）
2. agent 初审：结构规范、相对路径、frontmatter、是否更新 README
3. 维护者终审：策略逻辑正确性、防未来函数、QMT 实际可运行性
4. 合并用 squash，保持 master 历史一条线

## 新技能发布流程

每上线一个新技能：

1. `skills/<name>/` 入库，README 技能表从「规划中」改「可用」
2. `npx skills-ref validate` + `claude plugin validate .` 过一遍
3. bump 版本：`kimi.plugin.json` 的 `version`，打 tag（`v0.x.0`，minor 对应新技能，patch 对应修复）
4. 发 GitHub Release，写清：新技能解决什么问题、一条安装命令、一个使用示例
5. 关闭对应的 `skill-request` issue，并在 issue 里 @ 提需求的人

## 推广渠道（每个新技能发布后）

- skills.sh：用户 `npx skills add` 后自动上榜，无需操作
- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills)：首次发布后提一次 PR
- Claude 社区市场：platform.claude.com/plugins/submit
- 量化社区（知乎/雪球/QMT 用户群）按需分享

## 健康度自查（每月）

- [ ] 是否有超过一周无回应的 issue / PR
- [ ] README 技能表与 `skills/` 目录是否一致
- [ ] CI 是否仍然全绿（上游 skills-ref / claude CLI 可能更新）
- [ ] Discussions 里的高频问题是否值得沉淀进 README 或 FAQ
