from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth import get_user_model
import requests
import base64

# Create your models here.
User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.user)

    def get_default_avatar(self):
        if self.user.first_name or self.user.last_name:
            url = f"https://ui-avatars.com/api/?name={self.user.first_name}+{self.user.last_name}&format=svg&rounded=true&background=random"
        else:
            url = f"https://ui-avatars.com/api/?name={self.user.username}&format=svg&rounded=true&background=random"
        return "data:image/svg+xml;base64,"+base64.b64encode(requests.get(url).content).decode()