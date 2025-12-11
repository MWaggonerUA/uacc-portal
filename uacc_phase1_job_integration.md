# Phase 1 Job Integration Guide for `uacc-portal`

This document outlines a clean, scalable pattern for integrating
automated background jobs into the `uacc-portal` server environment. The
goal is to give you a layer-by-layer blueprint you can reuse for any job
(nightly refresh, PubMed harvesting, CCSG reporting, etc.), and to show
where each piece lives in your directory structure.

------------------------------------------------------------------------

## Overview of the Four Layers

A production-friendly job consists of four layers:

1.  **Business Logic (Python, inside app repo)**\
    Pure code that performs the actual work.

2.  **CLI Entrypoint (Python, inside app repo)**\
    A small wrapper that makes your business logic callable via
    `python -m ...`.

3.  **Shell Script (Bash, outside repo)**\
    A thin executable script that activates your venv, sets working
    directory, and runs the CLI.

4.  **systemd Unit + Timer (OS-level)**\
    Defines what to run (unit) and when to run it (timer).

------------------------------------------------------------------------

# Layer 1: Business Logic (Python, in `backend/services/`)

## Purpose

This layer performs the actual work: querying Aurora, calling PubMed
APIs, computing metrics, generating reports, writing Excel files, etc.

It should not contain: - CLI parsing\
- systemd/cron references\
- hardcoded paths\
- environment activation logic

## File Location

    apps/uacc-portal/backend/services/

## Example: `data_refresh.py`

``` python
# backend/services/data_refresh.py

from backend.services import aurora_sync, pubmed_sync, metrics

def refreshAllData():
    '''
    Orchestrates all nightly data refresh operations.
    '''
    aurora_sync.updateCoreTables()
    pubmed_sync.updateMemberPublications()
    metrics.recalculateProgramMetrics()
```

------------------------------------------------------------------------

# Layer 2: CLI Entrypoint (Python, in `backend/cli/`)

## Purpose

A CLI entrypoint: - Imports & calls your service code - Sets up
logging - Implements structured error handling - Returns appropriate
exit codes (0 = success, non-zero = failure)

## File Location

    apps/uacc-portal/backend/cli/

## Example: `refresh_all_data.py`

``` python
# backend/cli/refresh_all_data.py

import logging
import logging.config
import yaml
from pathlib import Path
from backend.services.data_refresh import refreshAllData

def setupLogging():
    config_path = Path(__file__).resolve().parents[2] / "config" / "logging.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    logging.config.dictConfig(config)

def main():
    setupLogging()
    logger = logging.getLogger(__name__)
    logger.info("Starting nightly data refresh")
    try:
        refreshAllData()
    except Exception:
        logger.exception("Nightly data refresh FAILED")
        raise
    else:
        logger.info("Nightly data refresh completed successfully")

if __name__ == "__main__":
    main()
```

------------------------------------------------------------------------

# Layer 3: Shell Script Runner (Bash, e.g. `~/scripts/cron/`)

## Purpose

The shell script: - Activates the venv\
- Sets environment paths\
- Changes to app directory\
- Calls the CLI using module syntax\
- Provides a simple command for systemd

## File Location

    /home/ec2-user/scripts/cron/

## Example: `refresh_all_data.sh`

``` bash
#!/usr/bin/env bash
set -euo pipefail

# Activate virtual environment
source /home/ec2-user/envs/portal-venv/bin/activate

# Navigate to application
cd /home/ec2-user/apps/uacc-portal

# Run CLI entrypoint
python -m backend.cli.refresh_all_data
```

------------------------------------------------------------------------

# Layer 4: systemd Service + Timer (OS-level)

## systemd Service Unit

    /etc/systemd/system/uacc-refresh.service

``` ini
[Unit]
Description=UACC Portal - Nightly data refresh
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=ec2-user
WorkingDirectory=/home/ec2-user/apps/uacc-portal
ExecStart=/home/ec2-user/scripts/cron/refresh_all_data.sh
```

------------------------------------------------------------------------

## systemd Timer Unit

    /etc/systemd/system/uacc-refresh.timer

``` ini
[Unit]
Description=Run nightly data refresh at 2:15am

[Timer]
OnCalendar=*-*-* 02:15:00
Persistent=true

[Install]
WantedBy=timers.target
```

------------------------------------------------------------------------

# Logging Strategy

## Python Logs (Your Code)

Captured via your `logging.yaml` configuration: - Job start/end - Major
steps - Warnings - Errors with stack traces

## systemd Logs

Captured via:

    journalctl -u uacc-refresh.service

Includes: - Service events\
- stdout/stderr from Python\
- Exit codes

------------------------------------------------------------------------

# Error Handling Strategy

## In Business Logic

-   Raise exceptions on failures.

## In CLI Entrypoint

-   Catch exceptions, log via `logger.exception`, then `raise`.

## In Shell Script

-   `set -euo pipefail` ensures failures propagate.

## In systemd

-   Non-zero exit → service marked failed.

------------------------------------------------------------------------

# Scaling to Multiple Jobs

Repeat this 4-layer pattern for each new job:

### Services

    backend/services/monthly_reports.py

### CLI

    backend/cli/generate_monthly_reports.py

### Shell Script

    scripts/cron/generate_monthly_reports.sh

### systemd

    uacc-monthly-reports.service
    uacc-monthly-reports.timer

------------------------------------------------------------------------

This structure ensures clean separation of concerns, clear logging,
reliable scheduling, and easy scaling.
