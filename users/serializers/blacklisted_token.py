from rest_framework import serializers
from users.models import BlacklistedAccessToken


class BlacklistedAccessTokenMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlacklistedAccessToken
        fields = ['jti', 'user', 'expires_at']


class BlacklistedAccessTokenCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlacklistedAccessToken
        fields = ['jti', 'user', 'expires_at']


class BlacklistedAccessTokenDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlacklistedAccessToken
        fields = '__all__'