from django.db import models
from django.contrib.auth.models import User


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    image = models.ImageField(upload_to='achievements/')

    def __str__(self):
        return self.name


# todo: think about real achievements and select items
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(blank=True, null=True, upload_to='users/avatars/')
    # achievements = models.ManyToManyField(Achievement, blank=True, related_name='users')

    @property
    def achievements(self):
        achievements = []
        if self.user.requests.count() >= 0:
            achievements.append(Achievement.objects.get(name='first_request'))
            achievements.append(Achievement.objects.get(name='test2'))
            achievements.append(Achievement.objects.get(name='test3'))
        return achievements
