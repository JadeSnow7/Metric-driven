# 前置最后的合同与共享样例补正

你是现有 coder 角色，不是唯一工作者。你独占 records/REIN-CH05-16/work/production 中的 ts/src/rein、ts/tests/rein-prerequisites.test.ts、rust/src/rein、rust/tests/prerequisites.rs、fixtures/cases/prerequisites.json 和 contracts/README.md；只在必要时调整 Rust lock/依赖。另一名 coder 正改仓库根 tools 和评估数据集，禁止触碰。v3 作者已终结，保留其代码和历史日志。证据写到 evidence/prerequisites-v4，不写正文、Loop或导航，不提交/推送/递归创建代理。

主线程已确认具体HTTP传输、全量70 TS/13 Rust测试已运行。不要重做架构，仅修下面的实际缺口并保留已有通过测试：

1. 现在 Rust 测试只从共享JSON读取 expected.hello，真正HTTP第一轮响应另写硬编码，TS/Rust没有使用同一响应数据。两端实际把 fixture.anthropic_response 和 fixture.openai_response 送进各自解析/回放/HTTP路径，断言统一预期。Rust loopback直接返回fixture.openai_response.to_string()，不要复制内容；第二轮请求用JSON解析断言完整 assistant tool_calls 和每个call ID对应的真实文件输出，不仅搜字符串。TS同样检查两条实际输出与其ID。
2. 将畸形响应列表放同一fixture，两端逐个读取并断言失败：数值id、数值name、空id/name、arguments数组/null/非JSON、tool_calls非数组、content非字符串或null以外的值。修正TS目前truthy数值id/name会接受、Rust非数组tool_calls被静默忽略和错误content被静默改空的情况。Anthropic同样校验id/name确为非空字符串。合法纯工具content:null仍应支持。
3. TS replay.receivedMessages 当前保存可变数组引用，调用者继续push会篡改过去请求。保存深拷贝；给两个请求各自历史测试。Rust现有replay函数可保留，文档不要声称存在相同capture接口。两端实际用同一Anthropic fixture验证system/text/tool_use/多个tool_result聚合，至少断言聚合后的两个ID。
4. 两端共享数据合同明确 optional字段输出：Rust Option字段序列化省略None，与TS optional一致，保留输入兼容null。补一个实际 serde->JSON与TS JSON的同一canonical样例断言（文件放fixture），不用运行器名称证明一致。tools工具错误按现有代码分类，正文前置README忠实写清错误码及 TS Error vs Rust Result、回放输入是Anthropic wire JSON而非ModelTurn对象、Rust具体HTTP入口。不要声称已隐藏全部路径错误细节，ch11会进一步处理。去掉未建立的标签用法承诺。

测试范围：保留旧功能，跑完整npm typecheck/test与Rust fmt/check/test（不得过滤），具体loopback若沙箱拒绝可请求该本地测试必要权限；原始输出和exit/hash保存到v4。返回逐项实际结果，不扩大改动。
