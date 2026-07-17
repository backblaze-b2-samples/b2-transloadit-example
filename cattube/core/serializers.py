from rest_framework import serializers

from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['title', 'uploaded_at', 'transcoded', 'thumbnail', 'user']


class NotificationSerializer(serializers.Serializer):
    transloadit = serializers.CharField(max_length=65536)
    signature = serializers.CharField(max_length=128)
