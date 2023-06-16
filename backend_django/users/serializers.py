from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from users.models import Profile, Achievement
from sorl.thumbnail import get_thumbnail


class LoginSerializer(serializers.Serializer):
    """
    This serializer defines two fields for authentication:
      * username
      * password.
    It will try to authenticate the user with when validated.
    """
    username = serializers.CharField(
        label="Username",
        write_only=True
    )
    password = serializers.CharField(
        label="Password",
        # This will be used when the DRF browsable API is enabled
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )

    def validate(self, attrs):
        # Take username and password from request
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            # Try to authenticate the user using Django auth framework.
            user = authenticate(request=self.context.get('request'),
                                username=username, password=password)
            if not user:
                # If we don't have a regular user, raise a ValidationError
                msg = 'Access denied: wrong username or password.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Both "username" and "password" are required.'
            raise serializers.ValidationError(msg, code='authorization')
        # We have a valid user, put it in the serializer's validated_data.
        # It will be used in the view.
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'username',
        ]


class AchievementSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Achievement
        fields = [
            'name',
            'description',
            'image',
        ]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)
    groups = serializers.SerializerMethodField()
    achievements = AchievementSerializer(many=True)

    def get_groups(self, obj):
        return obj.user.groups.values_list('name', flat=True)

    class Meta:
        model = Profile
        fields = [
            'user',
            'groups',
            'achievements',
        ]
        extra_kwargs = {
            'achievements': {'read_only': True},
        }


class ProfileAvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField()
    avatar_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'avatar',
            'avatar_thumbnail',
        ]
        extra_kwargs = {
            'avatar': {'write_only': True},
            'avatar_thumbnail': {'read_only': True},
        }

    def get_avatar_thumbnail(self, obj):
        if not obj.avatar:
            return None
        return get_thumbnail(obj.avatar, '100x100', crop='center', quality=99).url


