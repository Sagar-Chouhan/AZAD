#!/bin/bash
cd /home/azad-mis/azad-mis-backend
set -a; . ./.env; set +a
exec nohup ./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8080 >> uvicorn.log 2>&1 < /dev/null
