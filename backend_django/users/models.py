from django.contrib.auth.models import User
from django.db import models


class Team(models.Model):
    gitea_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=1000)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='teams')

    def __str__(self):
        return self.name


class Organization(models.Model):
    gitea_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=1000)
    avatar = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.URLField(blank=True, null=True)
    teams = models.ManyToManyField('Team', related_name='members', blank=True)

    def get_organizations(self):
        return Organization.objects.filter(teams__members=self).distinct()


class GiteaUser(models.Model):
    gitea_id = models.IntegerField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    avatar = models.URLField(blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gitea_user', blank=True, null=True)

    def __str__(self):
        return self.username


class AchievementDefinition(models.Model):
    slug = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1000)
    icon = models.CharField(max_length=200)
    threshold = models.IntegerField(default=1)
    category = models.CharField(max_length=50, default='general')
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'slug']

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='achievements')
    definition = models.ForeignKey(AchievementDefinition, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    date_earned = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('profile', 'definition')
        ordering = ['definition__sort_order']

    def __str__(self):
        return f'{self.profile.user.username} - {self.definition.name}'
