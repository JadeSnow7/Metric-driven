# 第 08 章独立示例

这个例子复制一份最小资料到临时目录，然后通过 Rust core 启动真实 Node 文件宿主，运行四种上下文方法。它不修改冻结 fixture，也不调用真实模型服务。

```sh
cd /绝对路径/book
node examples/ch08-context-methods/run.mjs
```

入口使用本目录的 `input/index.json`、`input/tasks.json` 和 `input/docs/note.md`，检查四行结果、真实 `read_file` 操作和来源前缀。
