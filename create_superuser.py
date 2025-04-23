import os
import django

#settingsモジュールのパス指定
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

#Django セットアップ
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

#任意のsuperuser情報
USERNAME = "admin"
EMAIL = "admin@example.com"
PASSWORD = "adminpass"

if not User.objects.filter(username=USERNAME).exists():
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print("Superuser created successfully!")
else:
    print("Superuser already exists.")
