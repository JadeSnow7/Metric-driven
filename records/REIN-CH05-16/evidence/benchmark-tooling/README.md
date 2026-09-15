# 后续章节基准工具

入口为 [`tools/rein_benchmark.py`](../../../../tools/rein_benchmark.py)。它只负责包装、调度和封存证据，不判断产品是否正确。

```sh
python3 tools/rein_benchmark.py prepare \
  --source /path/to/product --output /tmp/rein-prepared \
  --input /path/to/shared-product-input.md

python3 tools/rein_benchmark.py run \
  --coder /Users/huaodong/.codex/agents/coder.toml \
  --workspace /tmp/rein-prepared/control-arm --prompt /tmp/shared-prompt.md \
  --output /tmp/rein-run-control

python3 tools/rein_benchmark.py seal --tree /tmp/rein-run-control \
  --baseline /tmp/common-baseline --execution /tmp/rein-run-control/run.json \
  --output /tmp/rein-sealed-control

python3 tools/rein_benchmark.py review-pack --source /tmp/rein-sealed-control/tree \
  --mapping /tmp/reviewer-mapping.json --exclude run.json
```

`prepare` 保留完整产品快照中的公共基线，排除 Git、依赖、构建缓存和秘密环境文件，仅把 `.env.example` 保留下来；两臂 manifest 必须一致。额外 skill 文件只在准备清单中记录 hash，不复制进 control 臂。

`run` 每次只启动一个进程，首次返回后原样保存 JSONL、stderr、退出码和最终事件；主线程应分别调用两次以获得两臂并行。实际调用仍由主线程决定，因此本工具不会启动正式实验。

v2 修复后的焦点验证（原始命令退出码 0）：

```text
python3 -m unittest tools.tests.test_rein_benchmark -v
Ran 4 tests in 0.746s
OK
```

这组 fixture 实际覆盖已有 `task-inputs` 清理、真实 `.git/HEAD` 与 remote 去除、多行角色正文、stdin/CARGO_TARGET_DIR/`-o final.md`/usage/失败退出、过滤后的 patch 恢复、symlink manifest、两源四包以及 `package.json`/lockfile/fixtures manifest 保留。旧 v1 报告与输出保留在本目录的历史文件中。

限制：评审包映射和排除名单仍由主线程提供；工具不会判断产品正确性，也不会替代人工核查正文中的组别线索。依赖复制若需要，必须作为显式输入处理，且不进入产品 manifest。
