# 第08章独立示例

这是一个可复制的最小资料集。入口通过 `scripts/ch08-compare.mjs` 进入 Rust core，再由 core 通过既有协议启动真实 Node `read_file` 宿主。

```bash
node examples/ch08-context-methods/entry.mjs
```

它读取本目录的 `input/index.json`、`input/tasks.json`，输出四策略结果；不调用真实模型服务。
