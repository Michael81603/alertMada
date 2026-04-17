# confirmations/models.py
from django.db import models
from django.conf import settings

class Confirmation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='confirmations'
    )
    incident = models.ForeignKey(
        'incidents.Incident',
        on_delete=models.CASCADE,
        related_name='confirmations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'incident')  # Un user = une confirmation par incident

    def __str__(self):
        return f"{self.user.username} confirme incident #{self.incident.id}"