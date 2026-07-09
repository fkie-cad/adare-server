from django.contrib.auth.models import User
from rest_framework import serializers
from users.models import Profile, Organization, Team, GiteaUser, UserAchievement


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'email'
        ]


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'name',
            'description',
            'avatar',
        ]


class TeamSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(required=True)

    class Meta:
        model = Team
        fields = [
            'name',
            'description',
            'organization',
        ]


class AchievementSerializer(serializers.Serializer):
    name = serializers.CharField(source='definition.name')
    iconfile = serializers.CharField(source='definition.icon')
    description = serializers.CharField(source='definition.description')
    count = serializers.IntegerField()


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)
    teams = serializers.SerializerMethodField()
    avatar = serializers.URLField(required=True)
    achievements = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'user',
            'teams',
            'avatar',
            'achievements',
        ]

    def get_teams(self, obj):
        # Filter the teams where teams.organization.name == adare
        filtered_teams = obj.teams.filter(organization__name__iexact="adare")
        # Serialize the filtered teams
        return TeamSerializer(filtered_teams, many=True).data

    def get_achievements(self, obj):
        achievements = obj.achievements.select_related('definition').all()
        return AchievementSerializer(achievements, many=True).data


class GiteaUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiteaUser
        fields = [
            'username',
            'email',
            'avatar',
        ]