# Review check runner

`python3 run_check.py --cwd PATH --output NEW-DIR --timeout SEC -- COMMAND ARGS...` records the actual command, times, process result, raw output and SHA256 hashes of files under `cwd`. Generated metadata and common build/cache directories are excluded. A nonzero wrapper result means launch failure or timeout; this records local observable behavior and cannot prove strict OS isolation.
