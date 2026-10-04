# ch07 交付封存要求

仅正文验收通过后执行。生产根 `/private/tmp/rein-production-candidate-03` 不得替换/删除，冻结skill不得改。所有包装由单一coder执行。

调用 tools/rein_chapter_snapshot.py，source为生产根，chapter=07，output=records/REIN-CH05-16/snapshots/ch07-accepted，baseline=records/REIN-CH05-16/snapshots/ch06-accepted/files，portable-output=生产根/chapter-snapshots/rein-ch07.tar.gz。输出路径必须首次创建，拒绝覆盖。若Documents副本读取慢，可以使用root已独立验证与06快照逐文件完全一致的 `/private/tmp/rein-ch06-main-snapshot-review/tar-recovered/rein-ch06` 作为baseline，并在metadata明确路径与06manifest关系。不能换其他基线。

完整保留单次命令argv/cwd/start/end/exit/stdout/stderr。工具如果返回running就poll原session直到真实退出，禁止重启同一封存或手工补包。复制manifest与相邻patch进入chapter-snapshots，README仅讲读者恢复方法和对应章号；不得将生产评审/证据归档要求变成正文阅读步骤。根目录读者页应解释06旧observer注释只是本地可信钩子，不能承诺其禁止文件修改，避免改动已封存旧tar。

另归档 ch07 实际原始证据及历次保留源码：/private/tmp/rein-ch07-ts-evidence、rein-ch07-rust-evidence、rein-ch07-rust-final-evidence、rein-ch07-main-review-v1/v2/v3、rein-ch07-ts-v1-preserved、rein-ch07-ts-v2-preserved、rein-ch07-ts-v7-preserved、rein-ch07-ts-v8-preserved、rein-ch07-rust-v1-preserved、rein-ch07-rust-v2-preserved、rein-ch07-ts-body-evidence、rein-ch07-rust-body-evidence。不存在的源单列missing，不编造历史。记录source/relativepath/hash/mode；禁止node_modules/target/构建产品，只保留源码/夹具/运行原始输出及元数据。保留首次失败和后续修复，不覆盖旧记录。范围records/REIN-CH05-16/production/ch07/evidence。

主线程将独立恢复tar以及ch06+相邻patch、逐文件哈希/执行位比对后，才将07快照作为08共同起点。
