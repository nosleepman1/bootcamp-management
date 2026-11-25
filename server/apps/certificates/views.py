from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.permissions import IsAdminOrOrganizer, ReadOnlyOrHasRole
from .models import Certificate
from .serializers import CertificateSerializer


class ReadOnlyOrAdminOrOrganizer(ReadOnlyOrHasRole):
    allowed_roles = ("admin", "organizer")


@extend_schema_view(
    list=extend_schema(summary="Lister les certificats de fin de formation", tags=["Certificates"]),
    create=extend_schema(summary="Générer un certificat pour un apprenant", tags=["Certificates"]),
    retrieve=extend_schema(summary="Détail d'un certificat", tags=["Certificates"]),
    update=extend_schema(summary="Modifier un certificat", tags=["Certificates"]),
    partial_update=extend_schema(summary="Modifier partiellement un certificat", tags=["Certificates"]),
    destroy=extend_schema(summary="Supprimer un certificat", tags=["Certificates"]),
)
class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.select_related(
        "enrollment__user", "enrollment__cohort", "sent_by"
    ).all()
    serializer_class = CertificateSerializer
    permission_classes = [ReadOnlyOrAdminOrOrganizer]

    @extend_schema(
        summary="Envoyer le certificat à l'apprenant (passe le statut à ENVOYE)",
        responses={200: CertificateSerializer},
        tags=["Certificates"],
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminOrOrganizer],
        url_path="send",
    )
    def send(self, request, pk=None):
        certificate = self.get_object()
        certificate.status = Certificate.StatusCertificateEnum.SENT
        certificate.date_envoi = timezone.now()
        certificate.sent_by = request.user
        certificate.save(update_fields=["status", "date_envoi", "sent_by", "updated_at"])
        return Response(CertificateSerializer(certificate).data, status=status.HTTP_200_OK)
