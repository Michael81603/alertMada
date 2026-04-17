# incidents/models.py
from django.db import models
from django.conf import settings

class Incident(models.Model):
    TYPE_CHOICES = [
        ('route', 'Route dégradée'),
        ('inondation', 'Inondation'),
        ('accident', 'Accident'),
        ('eclairage', 'Éclairage défaillant'),
        ('dechet', 'Déchets'),
        ('autre', 'Autre'),
    ]
    STATUS_CHOICES = [
        ('signale', 'Signalé'),
        ('confirme', 'Confirmé'),
        ('en_cours', 'En cours de traitement'),
        ('resolu', 'Résolu'),
    ]
    PRIORITY_CHOICES = [
        ('vert', 'Vert - Faible'),
        ('orange', 'Orange - Moyen'),
        ('rouge', 'Rouge - Urgent'),
    ]

    IMPORTANCE_CHOICES = [
        (1, '1 - Peu important'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5 - Très important'),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_incidents'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    photo = models.ImageField(upload_to='incidents/%Y/%m/', blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='signale')
    priorite = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='vert')
    importance = models.PositiveSmallIntegerField(
        choices=IMPORTANCE_CHOICES,
        null=True,
        blank=True,
        help_text='Degré d’importance défini par une autorité (1-5)'
    )
    confidence_score = models.FloatField(default=0.0)  # Score de fiabilité 0-1
    confirmation_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['type']),
            models.Index(fields=['priorite']),
        ]

    def update_priority_from_score(self):
        """Calcule automatiquement la priorité selon le score de confiance.

        Si l'importance est définie manuellement, on ne modifie pas la priorité automatique.
        """
        if self.importance is not None:
            return
        if self.confidence_score >= 0.7:
            self.priorite = 'rouge'
        elif self.confidence_score >= 0.4:
            self.priorite = 'orange'
        else:
            self.priorite = 'vert'

    def set_importance(self, importance):
        self.importance = importance
        if importance >= 5:
            self.priorite = 'rouge'
        elif importance >= 3:
            self.priorite = 'orange'
        else:
            self.priorite = 'vert'

    def __str__(self):
        return f"[{self.type}] {self.description[:50]} - {self.statut}"

class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Commentaire de {self.user.username} sur incident {self.incident.id}"
