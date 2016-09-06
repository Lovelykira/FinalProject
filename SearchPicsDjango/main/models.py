from django.db import models

from django.contrib.auth.models import User


class Tasks(models.Model):
    status = models.CharField(max_length=500, default="IN_PROGRESS")
    keyword = models.CharField(max_length=500)
    date = models.DateField(auto_now=True)
    user = models.ForeignKey(User, null=True)


class Results(models.Model):
    task = models.ForeignKey(Tasks)
    link = models.CharField(max_length=2048)
    img = models.CharField(max_length=2048)
    rank = models.PositiveIntegerField()
    site = models.CharField(max_length=500)
