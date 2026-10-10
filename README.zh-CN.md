# Nanobug 插件市场

[English](README.md)

Nanobug 官方插件注册表与分发项目，英文名为 Nanobug-Plugin-Marketplace。

工单 01 实现审核注册表发布及 Nanobug 原生首次安装。下载统计、更新提示和版本管理属于工单 02；正式插件迁移属于工单 03–04。实际交付状态见[验收记录](docs/verification/01-reviewed-install-2026-10-10.md)。

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

## 构建与投稿

目录构建器和测试仅需 Python 3.11+：

```powershell
# 使用固定 ZIP 与 GitHub 夹具验证注册表约束。
python -m unittest discover -s tests -v
# 构建空目录；已有插件记录时追加 --validator <inspect_package.exe>。
python marketplace.py --output dist
```

通过 PR 提交[注册记录](registry/README.md)，每个版本均需人工审核。[归属转移](transfers/README.md)单独审核。PR 校验使用基线构建器及固定 Nanobug `Package` 校验器，不运行访客代码。在 Nanobug 仓库检出 `.github/validator.json` 固定的提交，以 `cargo build --locked -p plugin-runtime --example inspect_package` 构建校验器。

`Reviewed catalog` 工作流仅将 main 数据发布至 [catalog.json](https://t-miracle.github.io/Nanobug-Plugin-Marketplace/catalog.json)。Pages 来源须设为 **GitHub Actions**，仅上传 `dist/`，不建设独立网站。首个真实插件通过审核前，注册表保持为空；受控测试插件不发布。

原生客户端缓存目录及最后成功获取时间。刷新失败时禁止新市场安装，刷新成功后恢复。详情不加载 Markdown 内嵌图片、不解析 SVG 外部文件或网络引用；源码和反馈按钮打开已校验的 GitHub 仓库。安装须经过用户确认、SHA-256 与清单一致性、兼容性及工作区信任检查；工单 01 不允许在线重装已存在的 ID。
