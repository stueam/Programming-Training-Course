from django.db import models

class Singer(models.Model):
    name = models.CharField(max_length=100)
    intro = models.TextField()
    url = models.URLField()
    image = models.URLField(blank=True, default='')

class Song(models.Model):
    name = models.CharField(max_length=100)
    singer = models.ForeignKey(Singer, on_delete=models.CASCADE, related_name='song')
    url = models.URLField()
    image = models.URLField(blank=True, default='')
    lyrics = models.TextField(blank=True, default='')

class Comment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='comment')
    content = models.TextField()
    release_time = models.DateTimeField(auto_now_add=True)