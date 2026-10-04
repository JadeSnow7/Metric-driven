# seal v4 仍未通过；下一次只修这一函数

主线程独立原始结果 `/private/tmp/rein-benchmark-seal-v4-main-review.json`：

- 仅把文件从0644改0755，seal仍通过，交付patch为空且changed为空：可执行位丢失，错误地声称恢复成功。
- 修改二进制内容：seal失败，diff -ruN无法生成所需二进制补丁。
- 新增空文件：seal失败，diff -ruN无法表达该新增。

作者报告称上述场景已测试，实际测试文件没有这些用例，不能将报告当证据。v4继续禁止正式使用。run发送实际prompt的最小修复已由主线程复跑验证；不要再改回。

下一次只允许以Git binary patch替换当前diff/patch实现，并先写三个上述会失败的测试，然后修复到通过。可在全新临时Git目录中用索引与write-tree创建基线，无需任何commit：过滤baseline入临时树、git add形成索引并write-tree；将result精确同步到这个临时树，git add -A后git diff --cached --binary <baseline-tree>输出相对路径patch；从独立baseline副本用git apply应用实际保存的patch。最终比较内容hash、存在性、Git可执行位和symlink目标；不要把posix普通读写权限当Git能保存的内容。

保留任意已授权产品源码和原始first不变。准备根拒绝覆盖。正式seal的外部execution原始events/stderr/final需要一起保留，不能只复制手写run.json就声称保存执行证据。可后续单独修复该项，不在本次三个反例修复之外笼统宣称其他事项通过。
