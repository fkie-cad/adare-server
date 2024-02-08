from rest_framework import serializers
from knox.models import AuthToken


class KnoxTokenSerializer(serializers.ModelSerializer):
    token_key = serializers.CharField(read_only=True)

    class Meta:
        model = AuthToken
        fields = ('token_key',)


def create_token(token_model: AuthToken, user, serializer):
    # check if token for user already exists
    token = token_model.objects.filter(user=user).first()
    if token:
        # delete old token
        token.delete()

    # create new token
    instance, token = token_model.objects.create(user=user)
    return {"expiry": instance.expiry, "token": token}

