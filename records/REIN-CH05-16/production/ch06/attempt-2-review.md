# ch06 v2 主线程审查

状态：failed（生产返工，非对照首轮）。取消信号传输与Rust旧API兼容已有修复，但不满足完整行为门槛。

- 实际源码中 scripts/ch06-compare.mjs 仍只核对 reason；本机 CARGO_TARGET_DIR 硬编码在产品脚本。
- TS duplicate 两轮各一调用，Rust 同一轮给两调用；正常 Rust 输出固定“完成”，TS为一份真实内容，两版均未交付本章要求的三轮多文件正常例。
- 无工具间确定性取消演示；完整测试覆盖不足，不能据少量通过用例推定完整取消/预算行为。
- 两篇正文尚为v1草稿，后续独立作者在代码稳定后补写。

v2 18份源文件封存于 attempt-2-preserved/files，主线程逐项计算hash与manifest及当前源相等。v1/v2证据原样保留；v1缺源快照、部分起止时间为空均不补造。v3共同合同见 handoffs/ch06-final-contract.md。
