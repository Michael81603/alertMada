# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Notification

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'phone']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'reputation_score', 'created_at']
        read_only_fields = ['role', 'reputation_score', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    incident_id = serializers.IntegerField(source='incident.id', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'message', 'read', 'incident_id', 'created_at']
        read_only_fields = ['notification_type', 'message', 'incident_id', 'created_at']