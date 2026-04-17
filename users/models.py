from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = [
        ('citizen', 'Citoyen'),
        ('admin', 'Administrateur'),
        ('moderator', 'Modérateur'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    phone = models.CharField(max_length=20, blank=True)
    reputation_score = models.IntegerField(default=0)  # Score communautaire
    created_at = models.DateTimeField(auto_now_add=True)

    def is_admin_user(self):
        return self.role in ['admin', 'moderator']

    def __str__(self):
        return f"{self.username} ({self.role})"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('confirmed', 'Incident confirmé'),
        ('resolved', 'Incident résolu'),
        ('priority', 'Priorité modifiée'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    incident = models.ForeignKey(
        'incidents.Incident',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification({self.user.username}, {self.notification_type})"
