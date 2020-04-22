from django.contrib.auth.models import User
from django.db import models


class UserType(models.Model):
    type = models.CharField(max_length=32)

    def __str__(self):
        return self.type


class NewUserRequest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.ForeignKey(UserType, on_delete=models.CASCADE)


class UserUrl(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="url"
    )
    url = models.TextField()
