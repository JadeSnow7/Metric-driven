# IT-02 小模型实现合同

本文件是设计决定，不改变 SPEC.md 成功条件。等 SC-01/02 返回并审查后串行执行，共享脚本同一写入者。

## 1.3 权威表示

- 新增 `state.spec`：version、authority、source_ids、goal_ref、scope_ref、constraints、exceptions、conditions、contracts、open_items。
- goal_ref / scope_ref 可引用既有 discovery.expected_outcome / discovery.scope，条件引用既有 MET-*，验证方法/环境/输入/预期仍在对应 metric 定义；不手工复制一套 target/method。
- conditions 每项有稳定 `id`、非空 `metric_ids`、具体 `deliverables` 文件路径。每条都独立检查 metric 存在且强制/不退化；不能因其他条目有绑定而漏掉一项。contracts 是既有接口/正文 Spec 文件路径引用，内容字节被独立绑定。
- 模板展示上述复用。主线程人读 Spec 可以写在文件并由 contracts 引用，结构化条件只是可核验索引。

## 指纹

- 保留 1.1 与 1.2 的既有 revision 算法和各自语义。新增 `has_spec` 判断；不要把 1.2 视为 1.1。
- 1.3 产品 token + Spec 内容 digest 组合。Spec digest 包括完整 spec 声明、引用的 contracts 内容、所引用 discovery 字段、main task 规范定义、metric 的规范字段（kind/name/target/baseline/method/environment_data/verification 等）、receipt 分类与 foreign/external_inputs 声明。只在这些已知结构的精确位置排除运行状态/evidence_ids，禁止递归按名称删 result/status。
- 产品路径仍采用旧 Git 指纹基础；显式 deliverables 无论在 evidence/、摘要目录或被 Git ignore，都强制计算路径/类型/字节 hash。未生成文件可用 missing 标记，不阻止实施；验收时单独拒绝缺失。
- 新增 `binding.receipt_paths` 精确仓库相对文件路径作为运行回执排除；禁止目录吞并、非法路径与显式 deliverable/contract 冲突。分类本身纳入 Spec digest，改变分类先使旧证据失效。
- 没有 product diff 时也计算 Spec digest；state 位于仓库根目录、Spec位于元数据目录、Spec版本名未变三种情况不能漏。
- 每次 recorder 在前后重读状态，输出 Spec version/digest 与产品+Spec revision；验收输出明确 Spec version/digest。手写非执行证据须绑定 digest。旧证据缺少1.3绑定不得通过补改外层字段升级为已执行，需保留旧记录后重跑。

## 门槛与测试

- record 校验结构、引用、规范文件与字段有效性，implementation 校验就绪；此时不得要求计划中的交付物已存在。
- acceptance 逐条检查要求的 deliverable 存在、review范围覆盖、对应强制 metric 使用当前适用且 supports 对应指标的证据；再跑既有整体门槛。
- 正反例：正文/示例/运行产物任一遗漏拒绝；新增回执内容不改revision，编辑成功条件/metric method/相关产品/元数据目录中的Spec/raw同version都会失效；changed classification失效；契约文件不在Git差异列表也必须绑定；1.2自绑定、防重与全部既有检查继续通过。
- 一次状态生成方法可作为测试 helper，不改现有测试到新schema来隐藏兼容性。新的1.3测试独立文件。
