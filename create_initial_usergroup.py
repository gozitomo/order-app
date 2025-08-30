import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Import your Product model
from users.models import UserGroup

#任意のsuperuser情報
names = ["Forall", "A", "B"]

for name in names:
    if not UserGroup.objects.filter(name=name).exists():
        UserGroup.objects.create(name=name)
        print("UserGroup created successfully!")
    else:
        print("UserGroup already exists.")