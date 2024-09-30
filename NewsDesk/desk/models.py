from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


class Post(models.Model):
    pass


class Image(models.Model):
    pass


class Video(models.Model):
    pass


class Comment(models.Model):
    pass
