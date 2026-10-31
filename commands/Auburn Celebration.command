#!/bin/zsh
project_root="${0:A:h:h}"
cd -- "$project_root" || exit 1
PYTHONPATH="$project_root/src" /usr/bin/python3 -m reachy_customizations auburn "$@"
routine_status=$?
if (( routine_status != 0 )); then
  read -k 1 '?Press any key to close.'
fi
exit "$routine_status"
