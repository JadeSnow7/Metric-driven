import pathlib,sys
print(len(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines()))
