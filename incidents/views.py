# incidents/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Incident
from .serializers import (
    IncidentSerializer,
    IncidentCreateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
)
from .permissions import IsReporterOrAdmin
import math

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.select_related('reporter').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'statut', 'priorite']
    search_fields = ['description', 'type']
    ordering_fields = ['created_at', 'confidence_score', 'confirmation_count']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'nearby']:
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsReporterOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return IncidentCreateSerializer
        return IncidentSerializer

    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby(self, request):
        """
        Retourne les incidents dans un rayon donné.
        Params: lat, lon, radius_km (défaut: 5km)
        """
        try:
            user_lat = float(request.query_params.get('lat'))
            user_lon = float(request.query_params.get('lon'))
            radius_km = float(request.query_params.get('radius_km', 5))
        except (TypeError, ValueError):
            return Response(
                {"error": "Paramètres lat, lon requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filtre approximatif par bounding box (1° ≈ 111km)
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * math.cos(math.radians(user_lat)))

        incidents = Incident.objects.filter(
            latitude__range=(user_lat - lat_delta, user_lat + lat_delta),
            longitude__range=(user_lon - lon_delta, user_lon + lon_delta),
            statut__in=['signale', 'confirme', 'en_cours']
        )

        # Filtre précis avec Haversine
        def is_within_radius(incident):
            R = 6371
            dlat = math.radians(float(incident.latitude) - user_lat)
            dlon = math.radians(float(incident.longitude) - user_lon)
            a = (math.sin(dlat/2)**2 +
                 math.cos(math.radians(user_lat)) *
                 math.cos(math.radians(float(incident.latitude))) *
                 math.sin(dlon/2)**2)
            return R * 2 * math.asin(math.sqrt(a)) <= radius_km

        nearby_incidents = [i for i in incidents if is_within_radius(i)]
        serializer = IncidentSerializer(
            nearby_incidents, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='report-resolved',
            permission_classes=[permissions.IsAuthenticated])
    def report_resolved(self, request, pk=None):
        """Permet à un citoyen de signaler qu'un incident est terminé."""
        incident = self.get_object()
        user = request.user
        if incident.statut == 'resolu':
            return Response(IncidentSerializer(incident, context={'request': request}).data)

        is_reporter = incident.reporter == user
        has_confirmed = incident.confirmations.filter(user=user).exists()
        if not (is_reporter or has_confirmed):
            return Response(
                {"error": "Accès refusé. Vous devez être reporter ou avoir confirmé cet incident."},
                status=status.HTTP_403_FORBIDDEN
            )

        incident.statut = 'resolu'
        incident.save(update_fields=['statut'])
        if incident.reporter and incident.reporter != request.user:
            self._create_notification(
                incident.reporter,
                incident,
                'resolved',
                f"L'incident {incident.id} a été marqué comme résolu.",
            )
        return Response(IncidentSerializer(incident, context={'request': request}).data)

    def _create_notification(self, user, incident, notification_type, message):
        if not user:
            return
        from users.models import Notification
        Notification.objects.create(
            user=user,
            incident=incident,
            notification_type=notification_type,
            message=message,
        )

    @action(detail=True, methods=['patch'], url_path='set-importance',
            permission_classes=[permissions.IsAuthenticated])
    def set_importance(self, request, pk=None):
        """Permet aux autorités de définir l'importance d'un incident (1-5)."""
        if not request.user.is_admin_user():
            return Response({"error": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        incident = self.get_object()
        try:
            importance = int(request.data.get('importance'))
        except (TypeError, ValueError):
            return Response(
                {"error": "Importance invalide. Utilisez une valeur entière entre 1 et 5."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if importance < 1 or importance > 5:
            return Response(
                {"error": "Importance invalide. Choisissez une valeur entre 1 et 5."},
                status=status.HTTP_400_BAD_REQUEST
            )

        incident.set_importance(importance)
        incident.save(update_fields=['importance', 'priorite'])
        self._create_notification(
            incident.reporter,
            incident,
            'importance',
            f"L'importance de l'incident {incident.id} a été mise à jour.",
        )
        return Response(IncidentSerializer(incident, context={'request': request}).data)

    @action(detail=True, methods=['get', 'post'], url_path='comments',
            permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def comments(self, request, pk=None):
        incident = self.get_object()
        if request.method == 'GET':
            comments = incident.comments.select_related('user').all()
            return Response(CommentSerializer(comments, many=True).data)

        serializer = CommentCreateSerializer(
            data=request.data,
            context={'request': request, 'incident': incident}
        )
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        if incident.reporter and incident.reporter != request.user:
            self._create_notification(
                incident.reporter,
                incident,
                'comment',
                f"Un nouveau commentaire a été ajouté à l'incident {incident.id}.",
            )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='change-status',
            permission_classes=[permissions.IsAuthenticated])
    def change_status(self, request, pk=None):
        """Permet aux admins de changer le statut d'un incident."""
        if not request.user.is_admin_user():
            return Response({"error": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        incident = self.get_object()
        new_status = request.data.get('statut')
        if new_status not in dict(Incident.STATUS_CHOICES):
            return Response({"error": "Statut invalide."}, status=status.HTTP_400_BAD_REQUEST)
        incident.statut = new_status
        incident.save()
        return Response(IncidentSerializer(incident, context={'request': request}).data)