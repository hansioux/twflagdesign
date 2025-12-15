#!/bin/bash

# Activate virtual environment
source venv/bin/activate

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
# -w 4: 4 worker processes
# -b 0.0.0.0:8000: bind to all interfaces on port 8000
echo "Starting TW Flag Design App with Gunicorn on port 8000..."
exec gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
