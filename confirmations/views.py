# confirmations/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Confirmation
from incidents.models import Incident

class ConfirmIncidentView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, incident_id):
        try:
            incident = Incident.objects.get(id=incident_id)
        except Incident.DoesNotExist:
            return Response({"error": "Incident introuvable."}, status=status.HTTP_404_NOT_FOUND)

        # Empêcher le créateur de confirmer son propre incident
        if incident.reporter == request.user:
            return Response(
                {"error": "Vous ne pouvez pas confirmer votre propre signalement."},
                status=status.HTTP_400_BAD_REQUEST
            )

        confirmation, created = Confirmation.objects.get_or_create(
            user=request.user,
            incident=incident
        )

        if not created:
            return Response(
                {"message": "Vous avez déjà confirmé cet incident."},
                status=status.HTTP_200_OK
            )

        # Mettre à jour le score de confiance
        self._update_confidence_score(incident)

        # Récompenser le confirmateur (reputation)
        request.user.reputation_score += 1
        request.user.save(update_fields=['reputation_score'])

        return Response({
            "message": "Confirmation enregistrée.",
            "confirmation_count": incident.confirmation_count,
            "confidence_score": incident.confidence_score,
            "priorite": incident.priorite,
        }, status=status.HTTP_201_CREATED)

    def _update_confidence_score(self, incident):
        """
        Algorithme de score de confiance :
        - Basé sur le nombre de confirmations
        - Pondéré par le score de réputation des confirmateurs
        - Plafond à 1.0
        """
        confirmations = Confirmation.objects.filter(incident=incident).select_related('user')
        count = confirmations.count()

        # Score pondéré par réputation
        total_weight = sum(max(1, c.user.reputation_score) for c in confirmations)
        # Normalisation : log pour éviter l'inflation
        import math
        score = min(1.0, math.log(1 + total_weight) / 10)

        incident.confirmation_count = count
        incident.confidence_score = round(score, 3)
        incident.update_priority_from_score()
        incident.save(update_fields=['confirmation_count', 'confidence_score', 'priorite'])