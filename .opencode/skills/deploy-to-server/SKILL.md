---
name: deploy-to-server
description: Deploy latest changes to the remote homeauto server, restart the app service if successful.
---

## What I do

- SSH into `thomas@kjelpi.local`
- Change directory to `homeauto`
- Run `git pull` to fetch and update to the latest remote code
- Restart the homeauto systemd service (`sudo systemctl restart homeauto_app.service`)

## When to use me

Use this skill when you want to update and restart the homeauto application on your kjelpi.local server after a successful code push/merge.

## Usage

**Deploy latest code and restart the service:**
```bash
ssh thomas@kjelpi.local 'cd homeauto && git pull && sudo systemctl restart homeauto_app.service'
```

> Note: You must have SSH keys set up for thomas@kjelpi.local and sufficient sudo rights (may require password unless NOPASSWD is configured).

## Requirements
- `thomas@kjelpi.local` must be reachable from the local machine
- SSH key or password access must be configured
- The directory `homeauto` must exist on the remote
- The systemd service `homeauto_app.service` must be defined and active

## Example Output
```
Already up to date.
[sudo] password for thomas:
<service restart confirmation>
```
If there are updates:
```
Updating ab1cd23..ef456gh
Fast-forward
 ...
```
