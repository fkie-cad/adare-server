from django.contrib.auth.models import User
from rest_framework import serializers
from users.models import Profile, Organization, Team


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


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)
    teams = serializers.SerializerMethodField()
    avatar = serializers.URLField(required=True)

    class Meta:
        model = Profile
        fields = [
            'user',
            'teams',
            'avatar',
        ]

    def get_teams(self, obj):
        # Filter the teams where teams.organization.name == adare
        filtered_teams = obj.teams.filter(organization__name__iexact="adare")
        # Serialize the filtered teams
        return TeamSerializer(filtered_teams, many=True).data


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
        ]


class PublicProfileSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(required=True)
    teams = TeamSerializer(required=True, many=True)

    class Meta:
        model = Profile
        fields = [
            'user',
            'teams',
        ]

