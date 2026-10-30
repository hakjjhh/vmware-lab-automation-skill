# -*- coding: utf-8 -*-
"""vmrun 封装：免交互执行 / root 执行 / 屏幕打字 / 截图。用法见同目录 SKILL.md。

实践中的两条关键经验：
1) runProgramInGuest 不回传 guest stdout -> grun() 用 "重定向到临时文件 + copyFileFromGuestToHost"。
2) 命令串里带引号会被 vmrun/Windows 传参吃掉 -> 需要引号的命令一律写成脚本上传再执行（srun）。
"""
import io, os, subprocess, time

VMRUN = os.environ.get("VMRUN", r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe")
VMX = os.environ.get("VMX", "")
GU = os.environ.get("VMGU", "")
GP = os.environ.get("VMGP", "")
WORK = os.environ.get("VMWORK", os.path.join(os.path.expanduser("~"), "vm_work"))
SHOTS = os.path.join(WORK, "shots")
TMP = os.path.join(WORK, "tmp")
for _d in (WORK, SHOTS, TMP):
    os.makedirs(_d, exist_ok=True)
SD = os.path.dirname(os.path.abspath(__file__))
PW_G = "/tmp/.vmagent_pw"
CMD_G = "/tmp/.vmcmd.sh"
_seq = [0]


def run(args, timeout=300):\n    if not VMRUN:\n        raise RuntimeError("VMRUN is not configured")
    q = [VMRUN, "-T", "ws"] + list(args)
    p = subprocess.run(q, capture_output=True, timeout=timeout)
    return ((p.stdout or b"") + (p.stderr or b"")).decode("gbk", errors="replace").strip()


def _g(*a):\n    if not VMX or not GU or not GP:\n        raise RuntimeError("VMX, VMGU and VMGP must be configured")
    return ["-gu", GU, "-gp", GP] + list(a)


def _rid():
    _seq[0] += 1
    return "%d_%d" % (int(time.time()), _seq[0])


def copy_in(host, guest):
    return run(_g("copyFileFromHostToGuest", VMX, host, guest))


def copy_out(guest, host):
    return run(_g("copyFileFromGuestToHost", VMX, guest, host))


def graw(cmd, timeout=300):
    """执行，不取输出。cmd 里不要带引号。"""
    return run(_g("runProgramInGuest", VMX, "/bin/bash", "-c", cmd), timeout)


def grun(cmd, timeout=300):
    """普通用户执行并取回 stdout+stderr（cmd 不要带引号）。"""
    r = _rid()
    g, loc = "/tmp/.vmout_" + r, os.path.join(TMP, "vmout_" + r)
    graw("(%s) > %s 2>&1; echo exit=$? >> %s" % (cmd, g, g), timeout)
    copy_out(g, loc)
    graw("rm -f " + g)
    try:
        return io.open(loc, encoding="utf-8", errors="replace").read().strip()
    except Exception as e:
        return "ERR %s" % e


def _ensure_pw():
    loc = os.path.join(TMP, "pw.txt")
    io.open(loc, "w", encoding="utf-8", newline="\n").write(GP + "\n")
    copy_in(loc, PW_G)
    graw("chmod 600 " + PW_G)


def srun(cmd, timeout=600):
    """root 执行。cmd 可以随便带引号（走脚本文件）。"""
    _ensure_pw()
    loc = os.path.join(TMP, "cmd.sh")
    io.open(loc, "w", encoding="utf-8", newline="\n").write("#!/bin/bash\n" + cmd + "\n")
    copy_in(loc, CMD_G)
    graw("chmod +x " + CMD_G)
    r = _rid()
    g, h = "/tmp/.vmout_" + r, os.path.join(TMP, "vmout_" + r)
    graw("sudo -n true 2>/dev/null && sudo -n bash %s > %s 2>&1 || sudo -S bash %s < %s > %s 2>&1; echo exit=$? >> %s"
         % (CMD_G, g, CMD_G, PW_G, g, g), timeout)
    copy_out(g, h)
    graw("rm -f " + g)
    try:
        return io.open(h, encoding="utf-8", errors="replace").read().strip()
    except Exception as e:
        return "ERR %s" % e


def has_nopasswd():
    return "NOPASS_OK" in grun("sudo -n true 2>/dev/null && echo NOPASS_OK")


def bootstrap():
    """一次性写入 /etc/sudoers.d/vmagent，之后 root 免密。"""
    srun("echo '%s ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/vmagent && chmod 440 /etc/sudoers.d/vmagent" % GU)
    return "OK" if has_nopasswd() else "FAILED"


def shot(name, folder=None):
    path = os.path.join(folder or SHOTS, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    run(_g("captureScreen", VMX, path))
    return path


# ---------------- 屏幕打字 ----------------

def typer_ready():
    return "YES" in grun("test -f /tmp/last_done && echo YES || echo NO")


def start_typer():
    """上传并启动 typer（guest 桌面最大化终端，root 提示符）。"""
    for f in ("typer.sh", "launch_typer.sh"):
        copy_in(os.path.join(SD, f), "/tmp/" + f)
    srun("chmod +x /tmp/typer.sh /tmp/launch_typer.sh\n"
         "su - %s -c 'bash /tmp/launch_typer.sh' > /tmp/launch.log 2>&1" % GU)
    for _ in range(25):
        time.sleep(1)
        if typer_ready():
            return True
    return False


def _write_cmd(cmd):
    p = os.path.join(TMP, "next_cmd")
    io.open(p, "w", encoding="utf-8", newline="\n").write(cmd)
    copy_in(p, "/tmp/next_cmd")


def step(cmd, timeout=600, settle=0.8):
    """把命令打到屏幕上并等它执行完。"""
    _write_cmd(cmd)
    live = os.path.join(TMP, "last_done")
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            os.remove(live)
        except OSError:
            pass
        copy_out("/tmp/last_done", live)
        try:
            if io.open(live, encoding="utf-8", errors="replace").read().strip() == cmd.strip():
                time.sleep(settle)
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def fshot(name, cmd, folder=None):
    """清屏 -> 打命令 -> 截图。"""
    step("clear")
    time.sleep(0.4)
    step(cmd)
    time.sleep(0.6)
    return shot(name, folder)


# ---------------- 电源 ----------------

def vm_list():
    return run(["list"])


def vm_start(nogui=True, wait=120):
    r = run(["start", VMX] + (["nogui"] if nogui else []), timeout=300)
    for _ in range(wait // 5):
        time.sleep(5)
        if GU in grun("whoami"):
            return "started"
    return r


def vm_stop(mode="soft"):
    return run(["stop", VMX, mode], timeout=300)
