# 用 Python 统计 UTF-8 文件的行数

这个小例子读取一个 UTF-8 文本文件，并输出它的行数。每个由换行符分隔的文本行计数一次；空文件的行数是 `0`。

## 1. 准备文件

把下面两行保存为 `sample.txt`，文件编码选择 UTF-8，并让最后一行也以换行符结束：

```text
苹果
香蕉
```

同一目录中应有这三个文件：`README.md`、`count_lines.py` 和 `sample.txt`。

## 2. 运行示例

在该目录打开终端，运行：

```bash
python3 count_lines.py sample.txt
```

终端应只显示下面一行：

```text
2
```

程序的输出末尾有一个换行符。也可以把输出保存下来：

```bash
python3 count_lines.py sample.txt > result.txt
```

`result.txt` 应是 `2` 后跟一个换行符。可以用下面的命令核对：

```bash
python3 -c 'from pathlib import Path; print(repr(Path("result.txt").read_bytes()))'
```

应看到：

```text
b'2\n'
```

## 3. 代码怎样工作

`open(path, "r", encoding="utf-8")` 以 UTF-8 方式打开文件。`for _ in source` 逐行读取文件，`sum(1 for _ in source)` 把读取到的行数加起来。`print(line_count)` 输出数字并自动补上换行符。

如果省略文件参数，或指定的文件不存在，程序会把可理解的错误写到 stderr，并返回非零退出码：

```bash
python3 count_lines.py
python3 count_lines.py missing.txt
```

## 4. 自足练习

新建一个 UTF-8 文件 `practice.txt`，写入三行水果名称，并确保最后一行以换行符结束。运行：

```bash
python3 count_lines.py practice.txt
```

先写下你预计的数字，再用程序输出检查。最后清空 `practice.txt`，重新运行一次，确认空文件输出 `0`。
