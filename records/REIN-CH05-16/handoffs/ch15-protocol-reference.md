# ch15 固定协议参考

主线程于 2026-09-14 查阅下列 MCP 官方 2025-06-18 页面。本文件是后续 ch15 的产品规划输入，尚不表示 ch15 已实现或验证。

- 生命周期：首次交互为 initialize，交换版本、能力和实现信息；成功后客户端发送 notifications/initialized，再进行工具操作。只支持固定版本时，不兼容版本应断开。关闭 stdio 时先关闭输入并等待退出，必要时逐级终止；请求设超时，超时停止等待。[官方生命周期](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)
- 传输：客户端启动服务子进程，使用 UTF-8 JSON-RPC，每条消息占一行；JSON 字符串中的换行需要转义。stdout 专供协议，诊断使用 stderr。[官方 stdio 传输](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
- 工具：服务声明 tools 能力；tools/list 返回名称、描述与 inputSchema，tools/call 的参数为 name/arguments，结果含 content 及 isError。工具注解不能被当成授权依据。[官方工具规范](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)

本章仅实现文档检索所需的 stdio 子集，不把未实现的 HTTP、资源订阅、sampling、elicitation 或分页能力写成现有支持。两端代码和正文需要说明支持边界，并实际通过子进程通信完成发现及调用。
