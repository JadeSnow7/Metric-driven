# todo

命令行待办工具。

```bash
python3 -m todo add 买牛奶
python3 -m todo list
python3 -m todo export todos.csv
```

`export <路径>` 把所有待办写成 UTF-8 CSV，首行表头 `title,done`，`done` 为 `true`/`false`；含逗号、引号、换行的标题按 CSV 规则加引号转义。目标文件已存在会被覆盖；路径缺失或不可写时返回非零退出码。

数据文件默认是当前目录的 `todo.json`，可用环境变量 `TODO_FILE` 指定。命令模块列在 `todo/plugins.cfg`，启动时按行导入。

运行测试：`python3 -m unittest discover -s tests -v`
