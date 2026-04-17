# confirmations/urls.py
from django.urls import path
from .views import ConfirmIncidentView

urlpatterns = [
    path('<int:incident_id>/confirm/', ConfirmIncidentView.as_view(), name='confirm-incident'),
]