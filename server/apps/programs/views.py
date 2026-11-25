from uuid import UUID

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cohorts.models import Enrollment, TrainerAssignment
from apps.users.models import User
from apps.users.permissions import IsAdmin, ReadOnlyOrHasRole
from .models import Program, Project
from .serializers import ProgramSerializer, ProjectSerializer


class ReadOnlyOrAdminOrOrganizer(ReadOnlyOrHasRole):
    allowed_roles = ("admin", "organizer")


@extend_schema_view(
    list=extend_schema(summary="Lister tous les programmes", tags=["Programs"]),
    create=extend_schema(summary="Créer un programme", tags=["Programs"]),
    retrieve=extend_schema(summary="Détail d'un programme", tags=["Programs"]),
    update=extend_schema(summary="Modifier complètement un programme", tags=["Programs"]),
    partial_update=extend_schema(summary="Modifier partiellement un programme", tags=["Programs"]),
    destroy=extend_schema(summary="Supprimer un programme", tags=["Programs"]),
)
class ProgramViewSet(viewsets.ModelViewSet):
    """CRUD sur les programmes.

    - Écriture : réservée aux administrateurs.
    - Lecture : filtrée selon le rôle.
      - Admin/Organizer : tous les programmes.
      - Formateur : programmes des cohortes où il est affecté.
      - Apprenant : programmes des cohortes où il est inscrit.
    """

    queryset = Program.objects.all()
    serializer_class = ProgramSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role in (User.Role.ADMIN, User.Role.ORGANIZER):
            return super().get_queryset()
        if user.role == User.Role.TRAINER:
            program_ids = TrainerAssignment.objects.filter(
                user=user,
                status=TrainerAssignment.StatusEnum.ACTIVE,
            ).values_list("cohort__program_id", flat=True)
            return super().get_queryset().filter(id__in=program_ids)
        if user.role == User.Role.LEARNER:
            program_ids = Enrollment.objects.filter(
                user=user,
                status=Enrollment.StatusEnum.ACTIVE,
            ).values_list("cohort__program_id", flat=True)
            return super().get_queryset().filter(id__in=program_ids)
        return super().get_queryset().none()


@extend_schema_view(
    list=extend_schema(summary="Lister les projets pédagogiques", tags=["Projects"]),
    create=extend_schema(summary="Créer un projet lié à un programme", tags=["Projects"]),
    retrieve=extend_schema(summary="Détail d'un projet", tags=["Projects"]),
    update=extend_schema(summary="Modifier un projet", tags=["Projects"]),
    partial_update=extend_schema(summary="Modifier partiellement un projet", tags=["Projects"]),
    destroy=extend_schema(summary="Supprimer un projet", tags=["Projects"]),
)
class ProjectViewSet(viewsets.ModelViewSet):
    """CRUD sur les projets d'un programme. Lecture ouverte aux utilisateurs authentifiés, écriture Admin/Organizer."""

    queryset = Project.objects.select_related("program").all()
    serializer_class = ProjectSerializer
    permission_classes = [ReadOnlyOrAdminOrOrganizer]

    def get_queryset(self):
        queryset = super().get_queryset()
        program_id = self.request.query_params.get("program")
        if program_id:
            try:
                UUID(program_id)
            except ValueError:
                raise ValidationError({"program": ["UUID invalide."]})
            queryset = queryset.filter(program_id=program_id)
        return queryset

