# Project Cleanup

This document explains how to keep the project clean and what files can be safely removed.

## Already Cleaned Up

The following types of files have been removed:

1. **Python Cache Files**: All `__pycache__` directories and `.pyc` files
2. **Temporary/Backup Files**: Any `.bak`, `.swp`, etc. files

## Using the Cleanup Script

A cleanup script has been created to help maintain the project cleanliness:

```bash
# Run the cleanup script
./cleanup.sh
```

This script will remove:
- Compiled Python files (`__pycache__`, `.pyc`, etc.)
- Log files (`.log`)
- Backup files (`*~`, `.bak`, `.swp`, etc.)
- IDE-specific files (`.idea`, `.vscode`, etc.)

## Files to Add to .gitignore

Make sure the following patterns are in your `.gitignore` file:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Logs
*.log
logs/

# Database
instance/*.db
instance/*.sqlite
instance/*.sqlite3
!instance/securedeal_dev.db

# Rust
blockchain_services/target/
**/*.rs.bk

# Environment
.env
.venv
venv/
ENV/
.env.local

# IDE
.idea/
.vscode/
*.swp
*.swo
*~
```

## Important Files to Keep

The following files should NOT be deleted:

1. **Configuration Files**:
   - `config.py`
   - `docker-compose.yml` and `docker-compose.test.yml`
   - `.env` and `.env.example`

2. **Core Application Files**:
   - All files in `app/` except for `__pycache__` directories
   - `run.py`
   - `init_db.py`
   - `payment_monitor.py`

3. **Rust Backend**:
   - All files in `blockchain_services/src/`
   - `blockchain_services/Cargo.toml` and `blockchain_services/Cargo.lock`

4. **Documentation**:
   - `README.md`
   - `PITCH_READY.md`
   - `PROJECT_STRUCTURE.md`
   - `ENV_CONFIG_UPDATES.md`
