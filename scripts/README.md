# Crosswire Scripts

Utility scripts for managing Crosswire.

## Available Scripts

| Script | Description | Usage |
|--------|-------------|-------|
| `setup.py` | Initial project setup | `python scripts/setup.py` |
| `health_check.py` | Check service health | `python scripts/health_check.py` |
| `backup_state.py` | Backup state.json | `python scripts/backup_state.py` |
| `monitor.py` | Real-time monitoring | `python scripts/monitor.py` |
| `clean.py` | Cleanup temp files | `python scripts/clean.py` |
| `deploy.sh` | Docker deployment | `bash scripts/deploy.sh` |

## Quick Reference

```bash
# First time setup
python scripts/setup.py

# Check if everything is working
python scripts/health_check.py

# Start monitoring
python scripts/monitor.py

# Backup state before changes
python scripts/backup_state.py

# Clean up old files
python scripts/clean.py

# Deploy with Docker
bash scripts/deploy.sh
```
