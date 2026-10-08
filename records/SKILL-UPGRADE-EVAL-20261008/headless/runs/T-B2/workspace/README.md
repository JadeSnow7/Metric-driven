# todo

命令行待办工具。

```bash
python3 -m todo add 买牛奶
python3 -m todo list
python3 -m todo export todos.csv
```

`export <路径>` 把所有待办写成 UTF-8 CSV，表头为 `title,done`，`done` 取值 `true` / `false`；标题中的逗号、引号、换行按 CSV 规则转义。目标文件已存在时会被覆盖；路径无法写入时报错并返回 1。

数据文件默认是当前目录的 `todo.json`，可用环境变量 `TODO_FILE` 指定。命令模块列在 `todo/plugins.cfg`，启动时按行导入。

运行测试：`python3 -m unittest discover -s tests -v`
