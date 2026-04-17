# incidents/serializers.py
from rest_framework import serializers
from .models import Incident, Comment
from users.serializers import UserProfileSerializer
import math

class IncidentSerializer(serializers.ModelSerializer):
    reporter = UserProfileSerializer(read_only=True)
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'id', 'reporter', 'type', 'description',
            'latitude', 'longitude', 'photo', 'statut',
            'priorite', 'importance', 'confidence_score', 'confirmation_count',
            'created_at', 'updated_at', 'distance_km'
        ]
        read_only_fields = ['statut', 'priorite', 'importance', 'confidence_score', 'confirmation_count']

    def get_distance_km(self, obj):
        """Distance depuis la position de l'utilisateur (si fournie dans le contexte)."""
        request = self.context.get('request')
        if not request:
            return None
        try:
            user_lat = float(request.query_params.get('lat', 0))
            user_lon = float(request.query_params.get('lon', 0))
            if user_lat == 0 and user_lon == 0:
                return None
            # Formule de Haversine simplifiée
            R = 6371
            dlat = math.radians(float(obj.latitude) - user_lat)
            dlon = math.radians(float(obj.longitude) - user_lon)
            a = (math.sin(dlat/2)**2 +
                 math.cos(math.radians(user_lat)) *
                 math.cos(math.radians(float(obj.latitude))) *
                 math.sin(dlon/2)**2)
            return round(R * 2 * math.asin(math.sqrt(a)), 2)
        except (TypeError, ValueError):
            return None


class IncidentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ['type', 'description', 'latitude', 'longitude', 'photo']

    def create(self, validated_data):
        # Assigner automatiquement le reporter
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'incident', 'body', 'created_at']
        read_only_fields = ['user', 'incident', 'created_at']


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['body']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['incident'] = self.context['incident']
        return super().create(validated_data)
