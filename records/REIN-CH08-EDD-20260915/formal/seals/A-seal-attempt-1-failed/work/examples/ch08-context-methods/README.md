# 第08章独立示例

这个目录复制一份最小输入，调用仓库唯一的真实混合入口（Rust core → Node `read_file`）。在仓库根目录执行：

```bash
npm run --silent ch08:compare -- --data-root "$PWD/examples/ch08-context-methods/input"
```

它应输出四方法的 JSON；不会调用真实模型服务。输入可自由复制修改，原始冻结 fixture 不会被改动。
