# ch06 首次生产交付审查

结论：未通过，不是正式对照实验。作者正常结束并提交源码、两篇正文及六种reason对比；缺项按产品未完成记录，不作为资源中断。原始输出在 /private/tmp/rein-ch06-production-evidence；其commands.json的start/end为null，保留缺失，不由主线程补造。

主线程已全文读取双语言loop、TS loop测试、两个06示例、共享fixture、比较器、两正文及相关transport接口，并解析作者实际stdout。

- 跨语言比较只检查reason。实际duplicate场景TS派发2次模型、Rust只派发1次；ID与skip顺序不同。normal的TS答案包含真实文件文字，Rust固定返回“完成”。精确观察见attempt-1-parity-observations.json。
- TS只把signal传到ChatAdapter，OpenAI适配器与fetch Transport没有承接外部signal。raceControl在adapter.complete返回Promise后才注册监听，存在同步abort后遗漏信号的窗口。
- Rust在await_control得到Ok后没有再次检查取消/截止；同一poll中已经取消但返回的值可能被作为最终成功。循环末尾亦需防止max_turns掩盖已发生的取消/超时。是否能取消具体HTTP等待要看future释放/transport证据，不能仅从post没有signal参数推断不可取消。
- Rust ModelAdapter.complete新增必填参数，改变了05公共适配接口。应通过兼容的默认控制入口扩展，而不是只修改旧示例和测试来掩盖不兼容。
- TS loop测试10项实际含既有7项及新增3项，Rust4项均为05测试；缺同轮工具间取消、零工具预算、返回边界竞态及Rust06控制测试。六种CLI reason一致不能替代这些行为。
- 比较器和Rust正文硬编码本机Cargo target；正文的TS ch05命令把repo-relative fixture传给workspace内运行的CLI，目录会解析错。两个search-read锚点对应不同知识点；教材中还有主线程/实验专用等流程文字。

主线程要求v2先只修源码、fixtures、比较器和有区分力测试；两正文暂时停止修改，待代码稳定后交独立作者同步。旧首版证据及可恢复文件包保留，新的验证自动捕获时间、命令、退出码和原始输出。完整套件的localhost EPERM按既有授权做安全本地复跑，不删除断言或降低门槛。
