#!/bin/bash

# Activate virtual environment
# source venv/bin/activate
# export UV=''
export UV='uv run'

# Set environment variables (if not already set globally)
# You should ideally load these from a secure .env file using python-dotenv or similar in production
export FLASK_APP=run.py
export FLASK_ENV=production
# Export Google Auth Keys (Paste your credentials here)
export GOOGLE_CLIENT_ID='your-client-id-here'
export GOOGLE_CLIENT_SECRET='your-client-secret-here'

# Check for Google Auth keys
if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "WARNING: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET are not set."
    echo "Login functionality will not work."
fi

# Run Gunicorn
# -w 3: 3 worker processes (good for 1-2 cores)
# --threads 4: 4 threads per worker (handles I/O blocking like uploads better)
# --worker-class gthread: Use threaded workers
# --timeout 60: Increase timeout for image uploads (60 seconds)
echo "Starting TW Flag Design App with Gunicorn (Threaded) on port 8000..."
cd src
exec $UV gunicorn -w 3 --threads 4 --worker-class gthread --timeout 60 \
    --access-logfile ../log/gunicorn-access.log \
    --error-logfile ../log/gunicorn-error.log \
    -b 0.0.0.0:8000 "app:create_app()"
