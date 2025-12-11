# UACC Server Setup Summary
*A record of everything completed during initial configuration.*

## Overview
This server is a **UA-managed CCI Linux instance** in a private AWS subnet.  
It now hosts a **live FastAPI application** running as a persistent background service.  
All code is stored in a **GitHub repo**, deployed to the server via Git, and run inside a **Python virtual environment** managed via `systemd`.

This document captures the complete setup to-date.

## 1. Server Access & Authentication

### SSH Key Setup
- A private key (`uacc-server.pem`) was stored on your Mac under `~/.ssh/`.
- GitHub SSH authentication was configured on:
  - **Server**: using `~/.ssh/id_ed25519`
  - **Laptop (Mac)**: using `~/.ssh/id_ed25519`
- GitHub access was tested with:

```bash
ssh -T git@github.com
```

### Login Command

```bash
ssh -i ~/.ssh/uacc-server.pem ec2-user@uaccadmin-prd.colo-prod-aws.arizona.edu
```

### Result
You can now log into the server reliably from your Mac and interact with GitHub from both devices.

## 2. Directory Structure Created on the Server

These directories were created under your home folder:

```
~/apps
    └── uacc-portal
~/envs
~/config
    ├── env
    └── app
~/data
    ├── logs
    │   ├── portal
    │   └── cron
    ├── tmp
    └── exports
~/scripts
    ├── cron
    ├── maintenance
    └── one_off
~/notebooks
    ├── experiments
    └── scratch
~/bin
```

### Purpose Highlights
- `~/apps` → all deployable applications  
- `~/envs` → Python virtual environments  
- `~/config/env` → environment files with secrets  
- `~/data/logs` → logs for portal + cron jobs  
- `~/scripts` → scheduled tasks and maintenance tools  
- `~/bin` → small utility scripts  

## 3. Python Virtual Environment

A dedicated environment for your application:

```bash
python3 -m venv ~/envs/portal-venv
source ~/envs/portal-venv/bin/activate
pip install --upgrade pip
```

Installed dependencies:
- `fastapi`
- `uvicorn[standard]`

## 4. GitHub Repository Integration

### Repo Created
`uacc-portal` on GitHub under your `MWaggonerUA` account.

### Repo cloned to:
- **Your laptop**
- **Your server** (`~/apps/uacc-portal`)

### Workflow established
```bash
git add .
git commit -m "Message"
git push
# Then on server:
git pull
```

This is now the foundation of your deployment workflow.

## 5. Basic FastAPI Application

A minimal `app.py` was created with:

```python
@app.get("/")
def root():
    return {"message": "UACC portal is alive"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

A matching `requirements.txt` file was added.

## 6. Manual Run Tested

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Verified with:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
```

Both returned correct JSON responses.

## 7. `systemd` Service Created (Production-Ready)

Service file created at:

```
/etc/systemd/system/uacc-portal.service
```

Commands run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable uacc-portal
sudo systemctl start uacc-portal
sudo systemctl status uacc-portal
```

Verified healthy with:

```bash
curl http://127.0.0.1:8000/health
```

## 8. Security & Networking Notes

- Server is in a **private AWS subnet**
- SSH port forwarding is disabled by UA policy
- Port 8000 is not exposed externally
- UA Cloud team will later configure:
  - load balancer
  - Shibboleth (WebAuth)
  - HTTPS routing

## Summary

### ✔️ You now have:
- Fully configured SSH access  
- Git workflow  
- Server-side directory structure  
- A FastAPI app  
- A running background service  
- A stable deployment workflow  

### 🎉 Ready for:
- Real API routes  
- Database access  
- Logging  
- Internal dashboards  
- Scheduled tasks  
- Shibboleth integration  

# Development & Deployment Cycle (Compact)

1.  **Write/Update Code**

    -   Services → `backend/services/`\
    -   API routes → `backend/api/`\
    -   Job CLI → `backend/cli/`\
    -   Job shell script → `~/scripts/cron/`

2.  **Commit & Push**

    ``` bash
    git add .
    git commit -m "message"
    git push
    ```

3.  **Pull on Server**

    ``` bash
    cd ~/apps/uacc-portal
    git pull
    ```

    Update dependencies if needed:

    ``` bash
    source ~/envs/portal-venv/bin/activate
    pip install -r requirements.txt
    ```

4.  **Restart Web App (if backend changed)**

    ``` bash
    sudo systemctl restart uacc-portal.service
    ```

5.  **Add/Update Jobs**

    -   Place script in `~/scripts/cron/`\
    -   Install/modify `.service` and `.timer` under
        `/etc/systemd/system/`

    ``` bash
    sudo systemctl daemon-reload
    sudo systemctl enable --now jobname.timer
    ```

6.  **Test & Monitor**

    ``` bash
    sudo systemctl start jobname.service
    journalctl -u jobname.service -n 50 --no-pager
    systemctl list-timers | grep uacc
    ```

