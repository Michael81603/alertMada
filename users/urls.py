# users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    LogoutView,
    ProfileView,
    NotificationListView,
    NotificationMarkReadView,
    MyIncidentsView,
    MyActivityView,
    UserListView,
    UserUpdateRoleView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('my-incidents/', MyIncidentsView.as_view(), name='my_incidents'),
    path('my-activity/', MyActivityView.as_view(), name='my_activity'),
    path('admin/users/', UserListView.as_view(), name='user_list'),
    path('admin/users/<int:pk>/update-role/', UserUpdateRoleView.as_view(), name='user_update_role'),
]