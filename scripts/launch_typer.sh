#!/bin/bash
# 在 guest 桌面上开一个最大化终端跑 typer.sh：
#   - CentOS7: 无密码 sudo，靠 echo 密码 | su
#   - Ubuntu:  有 NOPASSWD sudo 时直接用 sudo，否则 su
UID_=$(id -u)
export DISPLAY=${DISPLAY:-:0}
if [ -z "$XAUTHORITY" ] || [ ! -f "$XAUTHORITY" ]; then
  for f in "$HOME/.Xauthority" /run/user/$UID_/gdm/Xauthority /run/user/$UID_/.mutter-Xwaylandauth.* /run/user/$UID_/xauth_*; do
    [ -f "$f" ] && export XAUTHORITY="$f" && break
  done
fi
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$UID_/bus}
PW="${VMPASS:-}"
pkill -f '[g]nome-terminal-server' 2>/dev/null
pkill -f '[t]yper.sh' 2>/dev/null
sleep 1
if sudo -n true 2>/dev/null; then
  RUN="sudo -n bash /tmp/typer.sh"
else
  if [ -z "$PW" ]; then
    echo "VMPASS is required when passwordless sudo is unavailable" >&2
    exit 1
  fi
  RUN="echo '$PW' | su -c 'bash /tmp/typer.sh'"
fi
setsid gnome-terminal --window --maximize -- bash -c "$RUN" </dev/null >/tmp/gt.log 2>&1 &
sleep 2
echo "launched XA=$XAUTHORITY DBUS=$DBUS_SESSION_BUS_ADDRESS"
