from rest_framework import serializers
from users.models import SecurityLog


class SecurityLogMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityLog
        fields = ['event_type', 'created_at', 'ip_address']


class SecurityLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityLog
        fields = ['user', 'event_type', 'ip_address', 'user_agent', 'details']


class SecurityLogDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityLog
        fields = '__all__'