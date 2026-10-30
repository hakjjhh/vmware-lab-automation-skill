---
name: vmware-workstation-lab-automation
description: Automate local VMware Workstation virtual machines on Windows for lab exercises, including power control, guest command execution, terminal screen typing, screenshots, NAT troubleshooting, and screenshot-based lab report generation. Use when the user asks to operate a local VMware VM, run commands inside a guest, capture evidence screenshots, or build an experiment report.
---

# VMware Workstation Lab Automation

A practical workflow for driving a local VMware Workstation VM on Windows with `vmrun`, guest-side shell scripts, terminal automation, and screenshots.

## Requirements

- VMware Workstation Pro with VMware Tools installed in the guest.
- Windows host with Python 3.
- A guest user with sudo/root access.
- `vmrun.exe`, normally at `C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe`.

## Configuration

Never hard-code credentials or machine-specific paths. Set these environment variables before using the helper:

| Variable | Meaning | Example |
|---|---|---|
| `VMRUN` | Path to `vmrun.exe` | `C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe` |
| `VMX` | Absolute path to the VM's `.vmx` file | `D:\vms\lab\Lab.vmx` |
| `VMGU` | Guest Linux username | `labuser` |
| `VMGP` | Guest password, supplied through the environment only | `<set locally>` |
| `VMWORK` | Host-side temporary/work directory | `%USERPROFILE%\vm_work` |

PowerShell example:

```powershell
$env:VMRUN = 'C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe'
$env:VMX   = 'D:\vms\lab\Lab.vmx'
$env:VMGU  = 'labuser'
$env:VMGP  = '<ask the user or read from a local secret store>'
$env:VMWORK = "$env:USERPROFILE\vm_work"
```

Do not commit `VMGP`, private keys, tokens, guest IP addresses, or personal VM paths to a public repository.

## Quick Health Check

```powershell
& $env:VMRUN -T ws list
& $env:VMRUN -T ws -gu $env:VMGU -gp $env:VMGP runProgramInGuest $env:VMX /bin/bash -c "whoami; hostname; ip -4 addr"
```

If the VM is not running:

```powershell
& $env:VMRUN -T ws start $env:VMX nogui
```

Wait 60–90 seconds, then check the guest again. A missing network address does not necessarily mean the VM failed to boot.

## Helper Script

`scripts/vmhelp.py` wraps the common operations:

```python
from vmhelp import *

print(vm_list())
print(grun("uname -a"))          # normal user, returns stdout/stderr
print(srun("systemctl status nginx"))  # root command through sudo
print(fshot("step_01.png", "ip -4 addr"))
```

Important implementation details:

1. `vmrun runProgramInGuest` does not reliably return guest stdout. `grun()` redirects output to a guest temp file and copies it back.
2. Quoting through Windows and `vmrun` is fragile. `srun()` writes the command to a script, uploads it, and runs it with `sudo -S`.
3. Chinese Windows may emit GBK. The helper decodes `vmrun` output as `gbk` with replacement.
4. Guest paths and host paths are kept separate through `copy_in()` and `copy_out()`.

## Root Access

The first run may need a password. `bootstrap()` writes `/etc/sudoers.d/vmagent`:

```python
from vmhelp import bootstrap
print(bootstrap())
```

This is a security-sensitive change. Run it only in a disposable lab VM, and remove it when finished:

```python
srun("rm -f /etc/sudoers.d/vmagent")
```

## Screen Typing for Natural-Looking Screenshots

Commands executed through `runProgramInGuest` do not appear in the guest terminal. To capture screenshots that show the command and its output:

1. Upload `scripts/typer.sh` and `scripts/launch_typer.sh` to `/tmp`.
2. Start the desktop typer with `start_typer()`.
3. Use `step()` or `fshot()`:

```python
step("clear")
step("ip -4 addr")
shot("network.png")
```

`typer.sh` watches `/tmp/next_cmd`, prints the command, evaluates it, and writes completion to `/tmp/last_done`. The host waits for that marker before taking a screenshot.

Tips:

- Put one command or short block per screenshot.
- Use `clear` before each new step.
- Keep commands short enough to remain visible.
- On X11 use a normal terminal; on Wayland, use a compatible terminal application or prefer text output without desktop typing.

## NAT and Network Recovery

Typical Windows host checks:

```powershell
Get-Service "VMware NAT Service"
Start-Service "VMware NAT Service"
```

Typical Linux guest checks:

```bash
ip -4 addr
ip route
cat /etc/resolv.conf
```

If the NAT adapter is present but has no route, restore the address and default gateway according to the VMware virtual network configuration. Avoid publishing real host/guest IP addresses; use placeholders in examples.

## Screenshots and Evidence

```python
shot("before.png")
fshot("after.png", "systemctl status my-service")
```

Use stable names such as `step_01_power.png`, `step_02_disk.png`, and `step_03_result.png`. Before delivery, crop excessive desktop borders and normalize image widths.

## Lab Report

Generate reports with `python-docx` and optionally export to PDF through Word COM or `docx2pdf`.

Suggested structure:

1. Title and author
2. Environment
3. Steps: screenshot + one-sentence explanation
4. Results
5. Summary

Before delivery, render the first page and spot-check for blank pages, cropped screenshots, and ordering errors.

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `vmrun list` has no VM | VM powered off or VMware service stopped | Start the VM and check VMware services |
| Guest command returns no output | `runProgramInGuest` does not relay stdout | Use the redirect-and-copy helper |
| Quotes disappear | Windows/vmrun argument parsing | Upload a script and execute the script |
| Screenshot is black | Locked desktop or no interactive session | Unlock the guest and restart the terminal helper |
| Screenshot shows only a prompt | Command was not echoed into the visible terminal | Use `start_typer()` and `step()` |
| Garbled Chinese output | GBK/UTF-8 mismatch | Decode host `vmrun` output as GBK; decode file output as UTF-8 |
| NAT unavailable | VMware NAT service or guest route is down | Check the service and restore the guest address/default route |

## Safety

- Use automation only on VMs the user owns or is authorized to operate.
- Treat passwords, private keys, tokens, and guest IPs as secrets.
- Ask before destructive commands such as disk formatting, snapshot deletion, or VM removal.
- Prefer disposable lab VMs for sudoers changes and destructive storage experiments.
- Keep generated credentials out of public skill repositories.

<!-- OB-S:Jy2hx4NX37Bq4buugu5Npg -->