# dashboard/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Q
from incidents.models import Incident
from users.models import User

class IsAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin_user()

class DashboardStatsView(APIView):
    permission_classes = [IsAdminPermission]

    def get(self, request):
        incidents = Incident.objects.all()
        stats = {
            "total_incidents": incidents.count(),
            "by_status": dict(
                incidents.values('statut')
                .annotate(count=Count('id'))
                .values_list('statut', 'count')
            ),
            "by_type": dict(
                incidents.values('type')
                .annotate(count=Count('id'))
                .values_list('type', 'count')
            ),
            "by_priority": dict(
                incidents.values('priorite')
                .annotate(count=Count('id'))
                .values_list('priorite', 'count')
            ),
            "urgent_count": incidents.filter(priorite='rouge').count(),
            "pending_count": incidents.filter(statut__in=['signale', 'confirme']).count(),
            "resolved_count": incidents.filter(statut='resolu').count(),
            "total_users": User.objects.count(),
            "top_reporters": list(
                User.objects.annotate(count=Count('reported_incidents'))
                .order_by('-count')[:5]
                .values('username', 'count', 'reputation_score')
            ),
        }
        return Response(stats)