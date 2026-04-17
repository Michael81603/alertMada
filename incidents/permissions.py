# incidents/permissions.py
from rest_framework import permissions

class IsReporterOrAdmin(permissions.BasePermission):
    """Seul le créateur de l'incident ou un admin peut modifier/supprimer."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin_user():
            return True
        return obj.reporter == request.user