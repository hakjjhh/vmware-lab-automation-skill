# VMware Workstation Lab Automation Skill

A ModelScope Agent Skill for automating local VMware Workstation labs on Windows.

It covers VM power control, guest command execution, sudo workflows, desktop typing, evidence screenshots, NAT troubleshooting, and screenshot-based report generation.

## Quick start

1. Install VMware Workstation Pro and VMware Tools.
2. Set `VMRUN`, `VMX`, `VMGU`, `VMGP`, and `VMWORK` in your environment.
3. Read `SKILL.md`.
4. Reuse `scripts/vmhelp.py`, `scripts/typer.sh`, and `scripts/launch_typer.sh`.

Credentials are never included in this repository. Use environment variables or a local secret manager.