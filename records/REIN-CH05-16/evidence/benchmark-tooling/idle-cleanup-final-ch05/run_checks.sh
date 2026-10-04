#!/bin/zsh
setopt no_nomatch
evidence_dir="/Users/huaodong/Documents/evidence-driven-development/records/REIN-CH05-16/evidence/benchmark-tooling/idle-cleanup-final-ch05"
log_name="$1"
shift
command_name="$1"
shift
args=("$@")
log_base="$evidence_dir/$log_name"
start="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
cwd="$(pwd -P)"
argv="$(printf '%q ' "$command_name" "${(@)args}")"
set +e
"$command_name" "${(@)args}" >"$log_base.stdout" 2>"$log_base.stderr"
exit_code=$?
set -e
end="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
{
  printf 'argv=%s\n' "$argv"
  printf 'cwd=%s\n' "$cwd"
  printf 'start=%s\n' "$start"
  printf 'end=%s\n' "$end"
  printf 'exit=%s\n' "$exit_code"
  printf 'stdout=%s\n' "$log_base.stdout"
  printf 'stderr=%s\n' "$log_base.stderr"
} >"$log_base.meta"
exit "$exit_code"
