# 首轮恢复相邻补丁（事后重建）

本目录以 `snapshots/pre-ch05-restored/files` 的 114 项精确 hash 源为 baseline，以 safe 首轮 arm-a / arm-b 的实际 files 目录为终点，重建 Git binary 相邻补丁。这里的“恢复”是基于原始 hash 的事后补丁重建，不改变首次产物、执行结果或成绩；原始空基线全新增补丁、execution 日志和 safe 目录均保留。

每个 arm 目录包含终点 manifest、补丁和真实独立 copy + `git apply --binary` 验证。验证同时比较文件内容、路径和 Git 可执行位；请以 `verification.json` 为证据。
