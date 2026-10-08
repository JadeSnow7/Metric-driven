# todo

命令行待办工具。

```bash
python3 -m todo add 买牛奶
python3 -m todo list
python3 -m todo export todos.csv   # 导出 CSV，列为 title,done
```

数据文件默认是当前目录的 `todo.json`，可用环境变量 `TODO_FILE` 指定。命令模块列在 `todo/plugins.cfg`，启动时按行导入。

运行测试：`python3 -m unittest discover -s tests -v`
