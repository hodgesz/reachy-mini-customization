#!/bin/zsh
cd -- "${0:A:h}" || exit 1
/usr/bin/python3 auburn_celebration.py
gesture_status=$?
if (( gesture_status != 0 )); then
  read -k 1 '?Press any key to close.'
fi
exit "$gesture_status"
