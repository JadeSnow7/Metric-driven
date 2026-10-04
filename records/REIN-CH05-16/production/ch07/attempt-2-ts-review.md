# TypeScript 第二轮复核

92/92完整测试raw已由root阅读，metadata已改用实际采时。独立重跑probe在 /private/tmp/rein-ch07-main-review-v2/ts-probe.json；除了 result-declares-call 仍错误成功派发外，其余已定位行为已修正。根因：validateHistory处理assistant多call后 i+=calls.length，工具结果跳过外层验证，所以外层新增tool.toolCalls检查根本覆盖不到已配对结果。必须直接验证results切片内每个结果的字段。现有4个ch07测试没有新增所要求的真实跨轮工具组场景，因此不能声称覆盖这些新输入。比较脚本虽改deep equality，但没有核算估算量/required组/动态答案，仍需要完成已授权验证范围；normalize应限定未承诺的result.error文案，不能全树递归清空所有名为error的字段。
