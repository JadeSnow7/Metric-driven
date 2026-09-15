# 完成双语言前置工程

你作为coder只负责production副本的最小前置工程。此前作者已停止，你不是唯一工作者，不要还原他人改动。唯一源码根为当前cwd，只可改ts/src/rein/**、ts/tests/rein-prerequisites.test.ts、rust/src/rein/**、rust/tests/prerequisites.rs、rust/Cargo.*、rust/src/lib.rs模块声明、contracts/README.md、fixtures/cases/prerequisites.json和fixtures/workspaces/prerequisites/**。另一coder在外部评估器路径工作，不能碰它。不得修改00–04正文、写05正文/Loop、原Agent-Learning、受测skill；不得commit/tag/push。不要再派子代理。

读取冻结skill ../../evidence/inputs/skill/tree/files/SKILL.md及必要references。现有前置不能验收，缺口必须完成，不可将其改名为限制：

- Rust有OpenAiHttp trait和openai_complete，但没有任何可真正发请求的实现。实现可用的ReqwestHttp或基于现有async-openai的等价具体传输，配置base_url/key/model、无应用级重试、有timeout；本机Cargo缓存确有reqwest 0.12.28，现有async-openai也依赖它。添加必要直接依赖后离线更新Cargo.lock，不得凭空宣称缺依赖。真实OpenAI请求必须保留完整assistant tool_calls及tool.tool_call_id。提供后续Loop可注入的统一模型接口及回放实现。
- 两语言Anthropic请求/响应必须处理system、text、tool_use、tool_result。纯工具回合不发送空text block，同轮多个tool结果组合为user内容块。拒绝无content字段、缺id/name、非对象arguments/input等畸形数据；纯工具响应合法。replay返回统一ModelTurn且能记录收到messages；不得仅处理text。
- 只读工具需有dispatchReadonly/execute_tool等公开路由：接受实际ToolCall、检查name和参数、真实执行read_file/search_files，并将返回toolCallId绑定调用id。不能用工具名冒充call id。已有便利函数可保留以兼容。两边完整目标realpath/canonicalize限制workspace，拒绝目录和symlinkescape；递归搜索文件内容稳定排序、不跟随symlink。错误合同两边一致。
- fixtures/cases/prerequisites.json是真正共享测试数据，两个语言测试都必须读取，不只是放在那里。测试至少覆盖纯工具、同轮两工具、多轮工具结果、坏arguments、缺id/name、未知工具、非法路径及symlinkescape、回放耗尽。

必须完成真实测试。现有Rust日志过滤rein::只执行2个旧测试并跳过tests/prerequisites.rs，不能作为本任务集成验收。新增Rust loopback HTTP捕获请求测试，走具体HTTP实现验证至少两个请求、第二轮assistant.tool_calls与tool_call_id；TS用受控Transport捕获同样协议。两版执行fixture工具结果并检查实际工作区内容。原hello回归也要跑。

验证命令在本cwd：npm run typecheck；npm test；cargo fmt --manifest-path rust/Cargo.toml -- --check；CARGO_TARGET_DIR=/private/tmp/rein-ch05-cargo-target cargo check/test --manifest-path rust/Cargo.toml --locked --offline（test不使用rein::过滤）。若本地监听被sandbox EPERM阻断，用自动审批请求可信本地回环测试；不得删除/skip测试来得出通过。无需真实外网模型，不读取密钥。

同步contracts/README，给清楚可用的接口用法。将stdout/stderr/exit、测试清单、修改文件hash与最终结果保存至 ../../evidence/prerequisites-v3/（允许写）；不覆盖v1/v2证据。返回实际结果，不把类型定义、trait或parser称为真实网络适配器。
