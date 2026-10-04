# Rein

《Rein：从零手写一个 Agent Harness》是一本面向 Agent 学习者与求职者的工程实践书。

## 仓库目录

书籍与配套代码共用本仓库：

| 目录 | 用途 | 当前状态 |
| --- | --- | --- |
| `docs/chapters/` | 00–16 章正文 | 01–03 章以 TypeScript 快速入门，Rust hello 可选；05–07 章已有 Rust core 与旧 TS 对照，06 plugin 教程已提供并完成离线实验核验，其余按混合路线规划 |
| `docs/readings/` | 阅读材料 0–3 | 阅读 0 与阅读材料 2 已提供；其余待撰写 |
| `docs/milestones/` | 第一阶段小结与三次阶段汇总 | 阶段汇总 1 已提供；其余待撰写 |
| `docs/appendices/` | 实现对照与深入讨论 A.1–A.5 | A.2 已提供；其余待撰写 |
| `ts/` | TypeScript 入门、Node host、领域插件与历史 loop 对照 | 第 01 章实现、host 与测试材料已落地 |
| `rust/` | Rust core 05–07、M1 stdio host 与测试 | core 与 M1 离线实验已核验 |
| `contracts/` | provider 模型适配合同与扩展进程通信合同 | 两条边界分别记录 |
| `fixtures/` | 共享验收输入、模型响应与 hybrid marker | 现有录制、工具输入和 hybrid marker 可按章节使用 |

影响长期结构的决定记录在 [DECISIONS.md](DECISIONS.md)；迁移记录入口为 [MIGRATIONS.md](MIGRATIONS.md)。

章节写作直接编辑对应 Markdown 文件。新增页面时同步更新 `docs/toc.md` 和 `docs/.vitepress/config.mts`；免费类型须与 [内容开放说明](docs/access.md) 一致。

## 本地阅读

```bash
npm ci
npm run dev
```

打开终端提示的本地地址即可预览。

## 运行代码

`ts/` 是根仓库的 npm workspace，与文档共用一次安装：

```bash
npm ci
npm test        # vitest
npm run typecheck
npm run hybrid:demo
npm run hybrid:verify
```

模型密钥复制 `ts/.env.example` 为 `ts/.env` 后填写，不入库。`tsx` 不会自动加载 `.env`，运行真实请求或录制命令时需显式传入 `--env-file=.env`；当前测试使用本地桩、内存数据及回环 HTTP 服务，不访问外网。

Rust 正式工程的验证在仓库根目录执行：

```bash
cargo test --locked --manifest-path rust/Cargo.toml
```

真实调用步骤见 [TypeScript 正文（修订中）](docs/chapters/01.md)和 [Rust 正文](docs/chapters/01-rust.md)。本地测试使用受控响应，不证明真实端点可用。

## 取某一章的代码

`ts/src/` 与 `rust/src/` 随正文演进。新版 SDK 教程使用第 01 章快照 `ch01-helloworld`：

```bash
git switch --detach ch01-helloworld
```

原 `ch01` 标签保留手写 HTTP 客户端、测试和两份录制，不包含新版 SDK 教程。`ch01-helloworld` 在本地交付；尚未推送时，新克隆的远程仓库取不到它，请使用交付的本地仓库。其余章节快照随章节完成并核验后建立。

阅读 0 已提供 [TypeScript 知识补充](docs/readings/00-ts.md)与 [Rust 知识补充](docs/readings/00-rust.md)，对应 `ts/examples/reading-00/` 与 `rust/examples/reading-00/` 中的可选示例。它们按需补充正文所需的基础知识，不是进入第 01 章的前置条件；安装依赖后无需密钥即可运行，具体命令见各版材料。专项测试需按材料中的命令单独运行，根目录 `npm test` 仍检查 TS 正式调用代码。

计划标注"可独立阅读"的后续章节会按模块职责在 `ts/examples/` 或 `rust/examples/` 提供自包含最小示例，不承诺两套完整 Harness，也不依赖主线累积状态。

## 构建与发布

```bash
npm run build
npm run preview
```

GitHub Pages 由 `.github/workflows/deploy.yml` 自动发布。推送到 `main` 或手动运行工作流都会构建 `docs/.vitepress/dist` 并部署。仓库设置中需要将 Pages 来源设为 **GitHub Actions**。代码测试由 `.github/workflows/test.yml` 在 `ts/`、`rust/`、`contracts/`、`fixtures/` 等相关路径变更时运行。

网站：https://jadesnow7.github.io/Rein/

当前仓库包含首页、阅读指南、规划目录、第 01 章 TypeScript 修订正文与 Rust 版本、阅读 0 的公共导读与双语言预备材料，以及 05–07 Rust core、Node host 和 hybrid M1 离线材料。`hybrid:demo` 与 `hybrid:verify` 是本地入口，最终全站放行仍需按证据记录核验。

本书目前限时免费。在持续更新过程中，部分限时免费章节将逐步转为收费；标注"永久免费"的章节将保持免费开放。具体收费范围、时间和价格以届时公告为准。GitHub 与 Pages 的公开历史会保留；政策说明不构成付费墙，未来付费交付将使用独立系统。

## 混合路线与历史入口

全书保留共同章节编号。01–03 章先用 TypeScript 建立调用直觉，Rust hello 是可选准备；从 05 章起，Rust core 负责权威运行时，TypeScript 负责宿主、SDK 和领域插件。04 章的 provider adapter contract 与后续 plugin stdio 是两种不同边界。当前入口见 [阅读指南](docs/about.md)与[完成状态](docs/toc.md)。

每个主题只在侧栏出现一次。语言按钮只出现在阅读 0 与第 01 章这两个确实拥有 TS/Rust 对应正文的主题；05–07 的 Rust core 页面与旧 TS 页面是主线和历史对照，不伪装成语言变体。核心小节和练习编号对齐，语言特有知识放在相关主题下。公共内容、正文、实现和验证进度分别说明，不用本地预备练习代替正式章节交付。历史 `ch01` 快照保持不变，新版使用单独标签。
