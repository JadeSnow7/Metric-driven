# common-20260915 共同工程交接

共同工程位于 `/private/tmp/rein-ch08-common-20260915/book`，由 Agent-Learning 当前 HEAD `1dfa82b9d90196c2294f61914d2017449e5548e3` 通过 `git clone --no-hardlinks --no-checkout` 建立后 checkout，再按验收快照逐文件物化。未创建新 commit。

## 核对材料

- `head.txt`：共同工程 HEAD；`original-head.txt`、`original-status.txt`、`original-dirty.patch`：原书 dirty 基线。
- `initial-verify.json`：161 个 book-initial 文件全部 hash 一致，未修改 `docs/chapters/01.md`。
- `fixture.sha256`：仅加入 `fixtures/ch08-context/index.json`、`tasks.json` 和 6 份 docs；未加入校准、历史记录或 EDD skill。
- `common-manifest.json`：共同工程相对路径、内容 hash 与 mode（排除 `.git`、`node_modules`、`target`）。
- `product-spec-ch08.md`：与 product-v3 spec 同 hash 的共同输入副本。

依赖从原工程复制到共同工程，未使用指向原工程的符号链接；`node_modules/.bin` 内部链接是 npm 依赖自身布局。正式组尚未启动。
