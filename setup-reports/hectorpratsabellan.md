# Setup report

- Generated: 2026-09-18 10:18 UTC
- Machine: Linux x86_64
- Login shell: /bin/bash
- Script ran under: bash 5.3.9(1)-release

## Needed to start the course

| Check | Status | Fix |
|---|---|---|
| uv installed (uv 0.12.16 (x86_64-unknown-linux-gnu)) | pass | — |
| Python 3.13 available to uv | pass | — |
| PyPI reachable (uv can install a package) | pass | — |
| git installed (2.53.0) | pass | — |
| git identity set (hector <hector.prats@alumni.esade.edu>) | pass | — |
| GitHub SSH authenticates | **FAIL** | add an SSH key to GitHub: `ssh-keygen -t ed25519 -C you@example.com`, then paste ~/.ssh/id_ed25519.pub at github.com/settings/keys |

## Needed by session 16 (containers)

| Check | Status | Fix |
|---|---|---|
| Docker daemon reachable | **FAIL** | install Docker Desktop with the WSL2 backend, enable WSL integration for your Ubuntu distro, and start it (not needed until session 16) |

**1 check(s) still needed to start the course are red.** Push this file anyway — it is a ticket. Bring it to the lab or to office hours.
