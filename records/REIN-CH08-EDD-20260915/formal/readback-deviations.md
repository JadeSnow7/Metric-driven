# 封存读回环境记录

B seal.py 正常完成后，主线程 Python 沙箱读回卡在 work/rust/tests/prerequisites.rs，lsof 已定位；该只读进程后来终止。提权单文件 shasum 成功，提权全文件 Python 读回最终完成：234文件、0差异，见 B-readback.json。期间另一全文件 shasum 调用45秒超时，未以超时认定内容错误。只清理已终结B的618M可再生成Cargo缓存，保留源码、原始运行和快照。C启动时其自身target为空；共享OS缓存与磁盘压力仍是环境差异。

本仓库普通git status只读查询也曾持续阻塞并被终止；未用空输出认定干净。原始命令与结果保留在主线程会话。
