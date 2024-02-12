from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.contrib.auth.models import User, PermissionsMixin
from django.utils.timezone import make_aware


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




# class AchievementCategory(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     description = models.CharField(max_length=1000)
#     iconfile = models.CharField(max_length=1000)
#
#     def __str__(self):
#         return self.name
#
#
# class Achievement(models.Model):
#     profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='achievements')
#     category = models.ForeignKey('AchievementCategory', on_delete=models.CASCADE, related_name='achievements')
#     date_earned = models.DateTimeField(auto_now=True)
#     date_updated = models.DateTimeField(auto_now_add=True)
#     count = models.IntegerField(default=0)
#
#
# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     avatar = models.ImageField(blank=True, null=True, upload_to='users/avatars/')
#
#     def update_achievements(self):
#         user_request_count = self.user.requests.count()
#         if user_request_count >= 1:
#             category = AchievementCategory.objects.get(name='first_request')
#             achievement, created = Achievement.objects.get_or_create(profile=self, category=category)
#             if achievement.count != user_request_count:
#                 # set updated date to now
#                 achievement.date_updated = make_aware(datetime.now())
#                 achievement.count = user_request_count
#                 achievement.save()
#             achievement.save()
#
#         accepted_experiment_count = self.user.requests.filter(status__name='accepted', category_type='experiment').count()
#         if accepted_experiment_count >= 1:
#             category = AchievementCategory.objects.get(name='first_accepted_experiment')
#             achievement, created = Achievement.objects.get_or_create(profile=self, category=category)
#             if achievement.count != accepted_experiment_count:
#                 # set updated date to now
#                 achievement.date_updated = make_aware(datetime.now())
#                 achievement.count = accepted_experiment_count
#                 achievement.save()
#             achievement.save()
#
#         accepted_scenario_count = self.user.requests.filter(status__name='accepted', category_type='scenario').count()
#         if accepted_scenario_count >= 1:
#             category = AchievementCategory.objects.get(name='first_accepted_scenario')
#             achievement, created = Achievement.objects.get_or_create(profile=self, category=category)
#             if achievement.count != accepted_scenario_count:
#                 # set updated date to now
#                 achievement.date_updated = make_aware(datetime.now())
#                 achievement.count = accepted_scenario_count
#                 achievement.save()
#             achievement.save()
