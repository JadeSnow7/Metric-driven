import argparse

parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument("--model")
parser.add_argument("--timeout-seconds", type=int)
