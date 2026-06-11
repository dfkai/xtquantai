## 改动说明

<!-- 这个 PR 做了什么？关联的 issue 用 "Closes #xx" -->

## 类型

- [ ] 新技能
- [ ] 改进现有技能
- [ ] 文档 / 安装说明
- [ ] 其他

## 新技能 / 技能改动自检清单

- [ ] 目录结构符合规范：`skills/<name>/SKILL.md`，脚本放 `scripts/`，长文档放 `references/`
- [ ] frontmatter 中 `name` 与目录名一致（小写字母/数字/连字符）
- [ ] 只使用标准 frontmatter 字段（`name`、`description`），未使用工具私有字段
- [ ] 文件间引用均为相对路径，无本机硬编码路径
- [ ] 本地通过 `npx skills-ref validate skills/<name>`
- [ ] 已更新 README 技能列表
- [ ] 涉及交易/回测逻辑的，已说明在哪个 QMT 环境验证过
