# 正文原始 shell 块（按正文逐字提取）

## Slate `docs/chapters/08.md`

```sh
npm run --silent ch08:compare
```

```sh
npm run --silent ch08:compare -- --budget 0
```

```sh
npm run --silent ch08:compare -- --data-root /tmp/rein-ch08-practice-1 --strategy on-demand
```

```sh
npm run --silent ch08:compare -- --data-root /绝对路径/book/fixtures/ch08-context --budget 0
```

```sh
npm run --silent ch08:compare -- --data-root /tmp/rein-ch08-practice-3 --strategy retrieval
```

## Larch `docs/chapters/08.md`

```bash
npm run --silent ch08:compare -- --data-root "$PWD/fixtures/ch08-context"
```

```bash
npm run --silent ch08:compare -- --strategy retrieval
npm run --silent ch08:compare -- --budget 0
```

```bash
tmp="$(mktemp -d)"; cp -R "$PWD/fixtures/ch08-context/." "$tmp/"; sed -i.bak 's/传输方式：JSON Lines/传输方式：Unix socket/' "$tmp/docs/early-runtime.md"; npm run --silent ch08:compare -- --data-root "$tmp" --strategy on-demand
```

```bash
npm run --silent ch08:compare -- --data-root "$PWD/fixtures/ch08-context" --budget 0
```

```bash
tmp="$(mktemp -d)"; cp -R "$PWD/fixtures/ch08-context/." "$tmp/"; sed -i.bak 's/最新发布文档中的检查命令是什么？/最新发布文档中的火星指标是什么？/' "$tmp/tasks.json"; npm run --silent ch08:compare -- --data-root "$tmp" --strategy retrieval
```

## Quartz `docs/chapters/08.md`

```bash
npm run --silent ch08:compare
```

```bash
npm run --silent ch08:compare -- --data-root /tmp/rein-ch08-practice-1 --strategy on-demand
```

```bash
npm run --silent ch08:compare -- --data-root /绝对路径/rein-ch08-practice-1 --budget 0
```

```bash
npm run --silent ch08:compare -- --data-root /绝对路径/rein-ch08-practice-1 --strategy retrieval
```

适配说明：Slate/Quartz 的占位路径和 Larch 的 `$PWD` 命令均按绝对 workspace 副本执行；Larch README 的真实命令与此前错误猜测的 `run.mjs` 分开记录。
