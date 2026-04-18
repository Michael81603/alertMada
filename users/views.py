# users/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserProfileSerializer, NotificationSerializer, UserAdminSerializer
from .models import User, Notification
from incidents.models import Incident
from incidents.serializers import IncidentSerializer, CommentSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Retourner les tokens directement à l'inscription
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserProfileSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Déconnexion réussie."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Token invalide."}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk=None):
        try:
            notification = Notification.objects.get(id=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        notification.read = True
        notification.save(update_fields=['read'])
        return Response(NotificationSerializer(notification).data)


class MyIncidentsView(generics.ListAPIView):
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Incident.objects.filter(reporter=self.request.user).select_related('reporter')


class MyActivityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        reported_incidents = Incident.objects.filter(reporter=request.user).select_related('reporter')
        comments = request.user.comments.select_related('incident', 'user').all()
        notifications = request.user.notifications.all()

        return Response({
            'reported_incidents': IncidentSerializer(reported_incidents, many=True, context={'request': request}).data,
            'comments': CommentSerializer(comments, many=True).data,
            'notifications': NotificationSerializer(notifications, many=True).data,
        })


class IsAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin_user()


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminPermission]


class UserUpdateRoleView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdminPermission]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        role = request.data.get('role')
        if role not in ['citizen', 'admin', 'moderator']:
            return Response({"error": "Rôle invalide."}, status=status.HTTP_400_BAD_REQUEST)
        instance.role = role
        instance.save()
        return Response(UserAdminSerializer(instance).data)