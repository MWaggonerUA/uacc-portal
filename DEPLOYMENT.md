# UACC Portal Deployment Guide

## Overview

This guide covers deploying the UACC Portal application to `uacc-portal.arizona.edu`. The application runs on a UA-managed CCI Linux server and is accessible via the domain once properly configured.

## Prerequisites

- SSH access to the server: `uaccadmin-prd.colo-prod-aws.arizona.edu`
- SSH key: `~/.ssh/uacc-server.pem`
- GitHub repository access
- The application is already set up with a systemd service

## Deployment Steps

### 1. Commit and Push Your Code

On your local machine (in the project directory):

```bash
# Check what files have changed
git status

# Add all changes
git add .

# Commit with a descriptive message
git commit -m "Add upload page functionality"

# Push to GitHub
git push
```

### 2. SSH into the Server

```bash
ssh -i ~/.ssh/uacc-server.pem ec2-user@uaccadmin-prd.colo-prod-aws.arizona.edu
```

### 3. Navigate to Application Directory

```bash
cd ~/apps/uacc-portal
```

### 4. Pull Latest Code

```bash
git pull origin main
```

(Or `git pull origin master` if your default branch is `master`)

### 5. Activate Virtual Environment

```bash
source ~/envs/portal-venv/bin/activate
```

### 6. Update Dependencies (if requirements.txt changed)

```bash
pip install -r requirements.txt
```

**Note:** Only run this if you've added or updated dependencies in `requirements.txt`. If you haven't changed dependencies, you can skip this step.

### 7. Restart the Application Service

```bash
sudo systemctl restart uacc-portal.service
```

### 8. Verify the Service is Running

```bash
# Check service status
sudo systemctl status uacc-portal.service

# Check if the app is responding
curl http://127.0.0.1:8000/health

# View recent logs
sudo journalctl -u uacc-portal.service -n 50 --no-pager
```

You should see:
- Service status: `active (running)`
- Health check response: `{"status":"ok","environment":"production"}` (or your configured environment)

### 9. Test the Application Endpoints

```bash
# Test root endpoint
curl http://127.0.0.1:8000/

# Test Dash app (should return HTML)
curl http://127.0.0.1:8000/dash
```

## Quick Deployment Script

For faster deployments, you can create a script on the server. SSH into the server and create:

```bash
nano ~/bin/deploy-portal.sh
```

Add this content:

```bash
#!/bin/bash
set -e

echo "Deploying UACC Portal..."

# Navigate to app directory
cd ~/apps/uacc-portal

# Pull latest code
echo "Pulling latest code..."
git pull

# Activate virtual environment
source ~/envs/portal-venv/bin/activate

# Update dependencies if needed
if [ -n "$(git diff HEAD@{1} requirements.txt 2>/dev/null)" ] || [ ! -z "$1" ]; then
    echo "Updating dependencies..."
    pip install -r requirements.txt
fi

# Restart service
echo "Restarting service..."
sudo systemctl restart uacc-portal.service

# Wait a moment for service to start
sleep 2

# Check status
echo "Checking service status..."
sudo systemctl status uacc-portal.service --no-pager -l

echo "Deployment complete!"
```

Make it executable:

```bash
chmod +x ~/bin/deploy-portal.sh
```

Then you can deploy with:

```bash
~/bin/deploy-portal.sh
```

Or to force dependency update:

```bash
~/bin/deploy-portal.sh --update-deps
```

## Domain Configuration

The application is currently running on port 8000 internally. For `uacc-portal.arizona.edu` to work:

1. **UA Cloud Team** needs to configure:
   - Load balancer pointing to your server
   - DNS record for `uacc-portal.arizona.edu`
   - HTTPS/SSL certificate
   - Shibboleth (WebAuth) authentication
   - Routing from port 443/80 to your internal port 8000

2. **You may need to provide:**
   - The internal server address: `uaccadmin-prd.colo-prod-aws.arizona.edu:8000`
   - Any specific routing requirements

Contact the UA Cloud team to complete the domain setup if it's not already configured.

## Troubleshooting

### Service Won't Start

```bash
# Check detailed error logs
sudo journalctl -u uacc-portal.service -n 100 --no-pager

# Check if port 8000 is in use
sudo lsof -i :8000

# Verify the service file
sudo cat /etc/systemd/system/uacc-portal.service
```

### Application Errors

```bash
# View real-time logs
sudo journalctl -u uacc-portal.service -f

# Check Python environment
source ~/envs/portal-venv/bin/activate
python --version
pip list
```

### Git Issues

```bash
# If you have uncommitted changes on server (shouldn't happen)
cd ~/apps/uacc-portal
git status
git stash  # Save changes
git pull
git stash pop  # Restore changes if needed
```

### Permission Issues

```bash
# Ensure you have proper permissions
ls -la ~/apps/uacc-portal
ls -la ~/envs/portal-venv
```

## Service Management Commands

```bash
# Start service
sudo systemctl start uacc-portal.service

# Stop service
sudo systemctl stop uacc-portal.service

# Restart service
sudo systemctl restart uacc-portal.service

# Check status
sudo systemctl status uacc-portal.service

# View logs
sudo journalctl -u uacc-portal.service

# View last 50 lines
sudo journalctl -u uacc-portal.service -n 50

# Follow logs in real-time
sudo journalctl -u uacc-portal.service -f

# Enable service to start on boot
sudo systemctl enable uacc-portal.service

# Disable service from starting on boot
sudo systemctl disable uacc-portal.service
```

## Environment Configuration

The application automatically loads configuration from:
- `~/config/env/uacc_db.env` (server deployment)
- Environment variables (highest priority)

### Database Configuration

**IMPORTANT:** The application requires a database configuration file to connect to MySQL.

Create the configuration file on the server:

```bash
mkdir -p ~/config/env
nano ~/config/env/uacc_db.env
```

Add the following (adjust values for your MySQL setup):

```bash
DB_HOST=localhost
DB_PORT=3306
DB_NAME=uacc_db
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
APP_ENV=production
```

**Note:** If MySQL is running on a different server, use that server's hostname or IP address instead of `localhost`.

Verify the configuration file exists and has correct settings:

```bash
cat ~/config/env/uacc_db.env
```

### Troubleshooting Database Connection Issues

If you encounter database connection errors:

1. **Run the diagnostic script:**
   ```bash
   cd ~/apps/uacc-portal
   source ~/envs/portal-venv/bin/activate
   python scripts/diagnose_db_connection.py
   ```

2. **Check MySQL is running:**
   ```bash
   sudo systemctl status mysql
   # or
   sudo systemctl status mariadb
   ```

3. **Test MySQL connection manually:**
   ```bash
   mysql -h localhost -P 3306 -u your_username -p your_database
   ```

4. **See detailed troubleshooting guide:**
   - `DB_CONNECTION_TROUBLESHOOTING.md` in the project root

After updating the configuration file, restart the service:

```bash
sudo systemctl restart uacc-portal.service
```

## Post-Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Code pulled on server
- [ ] Dependencies updated (if needed)
- [ ] **Database configuration file created** (`~/config/env/uacc_db.env`)
- [ ] **Database connection tested** (run `python scripts/diagnose_db_connection.py`)
- [ ] Service restarted
- [ ] Service status verified (active/running)
- [ ] Health check endpoint responds correctly
- [ ] Application endpoints tested
- [ ] **File upload and database write tested** (upload page with `write_to_db=true`)
- [ ] Logs checked for errors
- [ ] Domain accessible (if configured by UA Cloud team)

## Next Steps After Deployment

1. **Test the upload page** at `https://uacc-portal.arizona.edu/dash` (once domain is configured)
2. **Monitor logs** for any errors during initial use
3. **Verify file uploads** work correctly
4. **Check database connections** if database features are enabled
5. **Test authentication** once Shibboleth is configured

## Notes

- The application runs on port 8000 internally
- External access requires UA Cloud team configuration
- All code changes should go through Git (never edit directly on server)
- The service automatically restarts on server reboot (if enabled)
- Logs are available via `journalctl` for debugging
