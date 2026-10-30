# Lab Notes

Reusable patterns collected from VMware-based Linux lab work.

- RAID experiments: create a disposable virtual disk set, build the array with `mdadm`, format and mount it, then exercise fail/remove/add/recovery paths while collecting screenshots.
- Docker, Kubernetes, and OpenStack labs: reuse the same VM power-control, guest-command, screenshot, and report workflow.
- Adding a virtual disk: power off the VM, add the disk definition to the `.vmx` file, then start the VM and verify the device in the guest.
- Report template: title, environment, numbered screenshot steps, results, and summary.
- Prefer small commands and one screenshot per meaningful state transition.