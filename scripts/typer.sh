#!/bin/bash
# guest 侧"打字机"：宿主写 /tmp/next_cmd，这里回显并执行，完成后写 /tmp/last_done
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
rm -f /tmp/last_done 2>/dev/null
clear
P="${VMPROMPT:-[root@vm ~]# }"
printf '%s' "$P"
while true; do
  if [ -f /tmp/next_cmd ]; then
    C="$(cat /tmp/next_cmd)"
    D="$(cat /tmp/last_done 2>/dev/null)"
    if [ "$C" != "$D" ]; then
      printf '%s\n' "$C" | sed '1!s/^/> /'
      eval "$C"
      printf '%s' "$C" > /tmp/last_done
      printf '%s' "$P"
    fi
  fi
  sleep 0.3
done
