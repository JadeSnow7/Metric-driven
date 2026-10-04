# 实际导航检查，第一轮

主线程通过 CUA 在本机 VitePress dev 预览 `http://127.0.0.1:4175/Rein/` 实际操作，未访问已发布站点。默认窗口显示 Menu 折叠侧栏。

通过：

- 从 `/chapters/01.html#first-run` 点击 Rust，到 `/chapters/01-rust.html#first-run`，按钮状态更新。
- 在 Rust 页用键盘 Enter 激活 TypeScript，等待真实路由变为 `/chapters/01.html#first-run`；目标锚点存在，TypeScript aria-pressed 为 true。
- 从 `/readings/00-rust.html#types` 点击 TypeScript，到 `/readings/00-ts.html#types`；目标锚点存在，视口顶部位置约 109px。
- 打开 `/chapters/05-rust.html`，实际语言按钮数量为 0。

未通过：

- 打开 Menu 并展开“第二阶段 · 循环”，侧栏仍显示 05/06“待撰写”，链接仍为 `/chapters/05.html` 和 `/chapters/06.html`；没有 06-plugin 项。文稿代理的交接描述不能代替实际路由验收。已退回配置修复，修复后需再验。

运行环境：`npm ci --ignore-scripts --no-audit --no-fund` 成功安装 200 包；`cargo fetch --manifest-path rust/Cargo.toml` 经授权的 sandbox escalation 成功，新增 errno 与 signal-hook-registry 锁项。原 preview 命令在 sandbox 中 listen EPERM；改用仅监听 127.0.0.1 的 dev 预览并获自动批准，运行正常。此处不把这些安装或 UI 检查当成混合运行时验收。
