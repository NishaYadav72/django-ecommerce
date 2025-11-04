#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py makemigrations --no-input
python manage.py migrate --no-input

# 👇 Ye part add karo superuser auto-create ke liye
python manage.py shell <<EOF
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get("RENDER_SUPERUSER_USERNAME")
email = os.environ.get("RENDER_SUPERUSER_EMAIL")
password = os.environ.get("RENDER_SUPERUSER_PASSWORD")
if username and email and password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
EOF
