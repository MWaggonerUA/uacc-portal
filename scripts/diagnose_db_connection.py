#!/usr/bin/env python3
"""
Database connection diagnostic script.

This script helps diagnose database connection issues by:
1. Checking configuration file existence
2. Displaying current database settings (without passwords)
3. Testing database connectivity
4. Providing recommendations
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import settings, load_config
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


def check_config_file():
    """Check if configuration file exists and display its location."""
    home_dir = Path.home()
    config_paths = [
        home_dir / "config" / "env" / "uacc_db.env",
        project_root / ".env",
        home_dir / ".config" / "uacc" / ".env"
    ]
    
    print("=" * 70)
    print("CONFIGURATION FILE CHECK")
    print("=" * 70)
    
    found_files = []
    for config_path in config_paths:
        if config_path.exists():
            found_files.append(config_path)
            print(f"✓ Found: {config_path}")
        else:
            print(f"✗ Not found: {config_path}")
    
    if not found_files:
        print("\n⚠ WARNING: No configuration files found!")
        print("   The application will use default values (localhost, root, no password)")
        print(f"\n   Recommended: Create {home_dir / 'config' / 'env' / 'uacc_db.env'}")
    else:
        print(f"\n✓ Configuration loaded from: {found_files[-1]}")
    
    return found_files


def display_current_settings():
    """Display current database settings (masking password)."""
    print("\n" + "=" * 70)
    print("CURRENT DATABASE SETTINGS")
    print("=" * 70)
    
    # Reload config to ensure we have latest values
    config = load_config()
    
    print(f"DB_HOST:     {config.DB_HOST}")
    print(f"DB_PORT:     {config.DB_PORT}")
    print(f"DB_NAME:     {config.DB_NAME}")
    print(f"DB_USER:     {config.DB_USER}")
    print(f"DB_PASSWORD: {'*' * len(config.DB_PASSWORD) if config.DB_PASSWORD else '(empty)'}")
    print(f"APP_ENV:     {config.APP_ENV}")
    print(f"TEMP_DIR:    {config.TEMP_DIR}")
    
    # Show connection string (masked)
    password_display = "*" * len(config.DB_PASSWORD) if config.DB_PASSWORD else ""
    connection_string = (
        f"mysql+asyncmy://{config.DB_USER}:{password_display}"
        f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    )
    print(f"\nConnection String: {connection_string}")


async def test_connection():
    """Test database connection."""
    print("\n" + "=" * 70)
    print("DATABASE CONNECTION TEST")
    print("=" * 70)
    
    config = load_config()
    
    # Build connection string
    database_url = (
        f"mysql+asyncmy://{config.DB_USER}:{config.DB_PASSWORD}"
        f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    )
    
    print(f"Attempting to connect to: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
    print(f"User: {config.DB_USER}")
    
    try:
        # Create engine with short timeout for testing
        engine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5}
        )
        
        print("\nConnecting...")
        async with engine.begin() as conn:
            # Try a simple query
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✓ Connection successful!")
                
                # Try to get MySQL version
                try:
                    result = await conn.execute(text("SELECT VERSION()"))
                    version = result.fetchone()[0]
                    print(f"✓ MySQL Version: {version}")
                except Exception:
                    pass
                
                # Check if database exists and is accessible
                try:
                    result = await conn.execute(text("SELECT DATABASE()"))
                    db_name = result.fetchone()[0]
                    print(f"✓ Connected to database: {db_name}")
                except Exception:
                    pass
                
                return True
        
    except Exception as e:
        print(f"\n✗ Connection failed!")
        print(f"  Error: {type(e).__name__}: {str(e)}")
        
        # Provide specific recommendations based on error
        error_str = str(e).lower()
        if "connection refused" in error_str or "errno 111" in error_str:
            print("\n  💡 RECOMMENDATIONS:")
            print("     - MySQL server might not be running")
            print("     - MySQL might be on a different host (not localhost)")
            print("     - Check if MySQL is listening on the expected port")
            print("     - Verify firewall settings")
            print("\n  To check MySQL status:")
            print("     sudo systemctl status mysql")
            print("     # or")
            print("     sudo systemctl status mariadb")
        elif "access denied" in error_str or "authentication" in error_str:
            print("\n  💡 RECOMMENDATIONS:")
            print("     - Check username and password in config file")
            print("     - Verify user has access to the database")
        elif "unknown database" in error_str or "doesn't exist" in error_str:
            print("\n  💡 RECOMMENDATIONS:")
            print(f"     - Database '{config.DB_NAME}' doesn't exist")
            print("     - Create the database or update DB_NAME in config")
        elif "can't resolve hostname" in error_str or "name resolution" in error_str:
            print("\n  💡 RECOMMENDATIONS:")
            print(f"     - Cannot resolve hostname '{config.DB_HOST}'")
            print("     - Check DNS settings or use IP address instead")
        
        return False
    finally:
        try:
            await engine.dispose()
        except:
            pass


def provide_recommendations():
    """Provide recommendations for fixing database connection."""
    home_dir = Path.home()
    config_path = home_dir / "config" / "env" / "uacc_db.env"
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if not config_path.exists():
        print(f"\n1. Create configuration file: {config_path}")
        print("\n   Example content:")
        print("   " + "-" * 66)
        print("   DB_HOST=localhost")
        print("   DB_PORT=3306")
        print("   DB_NAME=uacc_db")
        print("   DB_USER=your_username")
        print("   DB_PASSWORD=your_password")
        print("   APP_ENV=production")
        print("   " + "-" * 66)
        print("\n   Or if MySQL is on a different server:")
        print("   DB_HOST=mysql-server.example.com")
        print("   DB_PORT=3306")
        print("   # ... rest of config")
    
    print("\n2. Verify MySQL is running:")
    print("   sudo systemctl status mysql")
    print("   # or")
    print("   sudo systemctl status mariadb")
    
    print("\n3. Test MySQL connection manually:")
    print("   mysql -h <host> -P <port> -u <user> -p <database>")
    
    print("\n4. Check MySQL bind address (if connection refused):")
    print("   sudo grep bind-address /etc/mysql/mysql.conf.d/mysqld.cnf")
    print("   # Should be 0.0.0.0 or 127.0.0.1 (not 127.0.0.1 if connecting from remote)")
    
    print("\n5. After fixing configuration, restart the application:")
    print("   sudo systemctl restart uacc-portal.service")


async def main():
    """Run all diagnostic checks."""
    print("\n" + "=" * 70)
    print("UACC PORTAL - DATABASE CONNECTION DIAGNOSTIC")
    print("=" * 70)
    print()
    
    # Check config files
    check_config_file()
    
    # Display current settings
    display_current_settings()
    
    # Test connection
    success = await test_connection()
    
    # Provide recommendations
    provide_recommendations()
    
    print("\n" + "=" * 70)
    if success:
        print("DIAGNOSIS COMPLETE: Connection is working!")
    else:
        print("DIAGNOSIS COMPLETE: Connection issues detected. See recommendations above.")
    print("=" * 70)
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

