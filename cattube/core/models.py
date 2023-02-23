from django.contrib.auth.models import User
from django.db import models


class Video(models.Model):
    title = models.CharField(max_length=256)
    assembly_id = models.CharField(max_length=256)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    transcoded = models.URLField()
    thumbnail = models.URLField()
    user = models.ForeignKey(User, related_name='videos', on_delete=models.CASCADE)

    def __str__(self):
        return f'"{self.title}", uploaded at {self.uploaded_at}, assembly_id {self.assembly_id}, transcoded {self.transcoded}, user {self.user.username}'


class Notification(models.Model):
    transloadit = models.CharField(max_length=65536)
    signature = models.CharField(max_length=40)
