#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py makemigrations --no-input
python manage.py migrate --no-input

# ✅ Safe superuser creation block
echo "Checking and creating superuser if needed..."
python manage.py shell <<'EOF'
import os
import django
django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get("RENDER_SUPERUSER_USERNAME")
email = os.environ.get("RENDER_SUPERUSER_EMAIL")
password = os.environ.get("RENDER_SUPERUSER_PASSWORD")

if username and email and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print("✅ Superuser created successfully.")
    else:
        print("ℹ️ Superuser already exists.")
else:
    print("⚠️ Missing environment variables for superuser.")
EOF
