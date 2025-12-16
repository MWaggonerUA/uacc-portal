# Database Connection Troubleshooting Guide

## Quick Diagnosis

If you're getting database connection errors, run the diagnostic script:

```bash
# On the server
cd ~/apps/uacc-portal
source ~/envs/portal-venv/bin/activate
python scripts/diagnose_db_connection.py
```

This will:
- Check if configuration files exist
- Display current database settings
- Test the database connection
- Provide specific recommendations

## Common Error: "Connection Refused"

**Error Message:**
```
Can't connect to MySQL server on 'localhost' ([Errno 111] Connection refused)
```

### Possible Causes & Solutions

#### 1. Configuration File Missing

The application looks for database configuration in:
- `~/config/env/uacc_db.env` (server deployment - **recommended**)
- `.env` in project root (development)
- `~/.config/uacc/.env` (local development)

**Solution:** Create the configuration file:

```bash
# On the server
mkdir -p ~/config/env
nano ~/config/env/uacc_db.env
```

Add the following (adjust values for your setup):

```bash
DB_HOST=localhost
DB_PORT=3306
DB_NAME=uacc_db
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
APP_ENV=production
```

**Important:** If MySQL is on a different server, use that server's hostname or IP address instead of `localhost`.

#### 2. MySQL Not Running

**Check MySQL status:**
```bash
sudo systemctl status mysql
# or
sudo systemctl status mariadb
```

**Start MySQL if not running:**
```bash
sudo systemctl start mysql
# or
sudo systemctl start mariadb
```

**Enable MySQL to start on boot:**
```bash
sudo systemctl enable mysql
```

#### 3. MySQL on Different Host

If MySQL is running on a different server (not localhost), update the configuration:

```bash
# In ~/config/env/uacc_db.env
DB_HOST=mysql-server.example.com  # Use actual hostname or IP
DB_PORT=3306
# ... rest of config
```

#### 4. MySQL Not Listening on Expected Port

**Check what port MySQL is using:**
```bash
sudo netstat -tlnp | grep mysql
# or
sudo ss -tlnp | grep mysql
```

**Check MySQL configuration:**
```bash
sudo grep port /etc/mysql/mysql.conf.d/mysqld.cnf
# or
sudo grep port /etc/my.cnf
```

Update `DB_PORT` in your config file if MySQL uses a different port.

#### 5. MySQL Bind Address Issue

If MySQL is only listening on 127.0.0.1, it might not accept connections properly.

**Check bind address:**
```bash
sudo grep bind-address /etc/mysql/mysql.conf.d/mysqld.cnf
```

**If you need to allow connections:**
- For localhost only: `bind-address = 127.0.0.1`
- For all interfaces: `bind-address = 0.0.0.0` (less secure)

After changing, restart MySQL:
```bash
sudo systemctl restart mysql
```

## Testing the Connection Manually

Test MySQL connection from command line:

```bash
mysql -h localhost -P 3306 -u your_username -p your_database
```

If this works, the issue is with the application configuration. If this fails, the issue is with MySQL setup.

## After Fixing Configuration

1. **Restart the application:**
   ```bash
   sudo systemctl restart uacc-portal.service
   ```

2. **Check service status:**
   ```bash
   sudo systemctl status uacc-portal.service
   ```

3. **View logs:**
   ```bash
   sudo journalctl -u uacc-portal.service -n 50 --no-pager
   ```

4. **Test the upload page again**

## Configuration File Locations (Priority Order)

The application loads configuration in this order (later overrides earlier):

1. Default values (localhost, root, no password)
2. `~/config/env/uacc_db.env` (server deployment)
3. `.env` in project root
4. `~/.config/uacc/.env` (local development)
5. Environment variables (highest priority)

## Security Notes

- Never commit configuration files with passwords to Git
- Use strong passwords for database users
- Restrict database user permissions to only what's needed
- Consider using environment variables for sensitive data in production

## Getting Help

If you're still having issues:

1. Run the diagnostic script: `python scripts/diagnose_db_connection.py`
2. Check application logs: `sudo journalctl -u uacc-portal.service -n 100`
3. Check MySQL logs: `sudo tail -f /var/log/mysql/error.log`
4. Verify MySQL is accessible: `mysql -h <host> -u <user> -p`

