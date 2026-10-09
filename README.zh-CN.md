# Nanobug 插件市场

[English](README.md)

Nanobug 官方插件注册表与分发项目，英文名为 Nanobug-Plugin-Marketplace。

当前仅完成已确认执行方案、四张实施工单、测试责任分配与协作规范的整理。市场功能尚未实现或部署。

## 范围

- 编辑器内插件发现、下载、下载次数、历史版本及兼容版本安装。
- 第三方公开开源插件通过 PR 审核收录。
- GitHub Pages 托管静态目录，各作者 GitHub Releases 托管 ZIP。
- 七个官方插件独立维护，最终编辑器发行不随附插件。
- 首版不做独立市场网页、评分、付费、私有插件来源或额外后端。

## 文档

- [文档入口](docs/README.md)
- [执行规格](docs/specs/plugin-marketplace.md)
- [四张工单与测试安排](docs/tickets/README.md)
- [议题发布记录](docs/tickets/publication.json)
- [AI 协作规范](AGENTS.md)

Nanobug 宿主负责原生界面与安装运行时；各插件仓库维护自己的源码与包；本仓库维护注册表、审核发布、统计和本主题的方案与工单。

实现阶段按实际引入的工具维护命令；当前文档项目不代表市场服务已可用。
