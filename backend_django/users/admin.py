from django.contrib import admin

from users.models import Profile, GiteaUser, Team, Organization


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'avatar']
    search_fields = ['user__username']
    raw_id_fields = ['user']


@admin.register(GiteaUser)
class GiteaUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email', 'gitea_id']
    search_fields = ['username', 'email']
    raw_id_fields = ['user']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'gitea_id', 'organization']
    search_fields = ['name']
    raw_id_fields = ['organization']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'gitea_id']
    search_fields = ['name']
