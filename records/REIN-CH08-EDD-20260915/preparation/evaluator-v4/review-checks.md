# 独立评审检查清单

- 实际运行默认 16 行、budget 0、事实变更、重复 metadata、缺失文件和 path escape；核对真实 stdout/stderr、退出码与行级状态。
- 阅读 Rust `context_methods` 的预算、策略、证据采纳和 Node `read_file` 边界；确认 callRecords 来自真实 StdioExecutor。
- 从最终 Markdown 逐条执行命令，跟做三项练习；核对参数、文件、输出、messages、来源、quality 和失败结论。
- 执行独立 example 与根 verify，检查真实混合进程；运行既有 TS/Rust 回归、05–07 compare、docs build/link/navigation。
- 产品质量不因缺少 EDD 记录格式扣分；自动 evaluator 不替代进程真实性、算法机制、正文复现和代码文字一致性评审。
