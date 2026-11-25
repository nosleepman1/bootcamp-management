from uuid import UUID

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.users.permissions import IsAdminOrOrganizerOrTrainer, ReadOnlyOrHasRole
from .models import Deliverable, ProjectAssignment
from .serializers import (
    DeliverableSerializer,
    GradeDeliverableSerializer,
    ProjectAssignmentSerializer,
)


class ReadOnlyOrStaffOrTrainer(ReadOnlyOrHasRole):
    allowed_roles = ("admin", "organizer", "trainer")


@extend_schema_view(
    list=extend_schema(summary="Lister les affectations de projets", tags=["Evaluations"]),
    create=extend_schema(summary="Assigner un projet à un apprenant", tags=["Evaluations"]),
    retrieve=extend_schema(summary="Détail d'une affectation de projet", tags=["Evaluations"]),
    update=extend_schema(summary="Modifier une affectation de projet", tags=["Evaluations"]),
    partial_update=extend_schema(summary="Mettre à jour le statut d'un projet", tags=["Evaluations"]),
    destroy=extend_schema(summary="Supprimer une affectation de projet", tags=["Evaluations"]),
)
class ProjectAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ProjectAssignment.objects.select_related(
        "enrollment__user", "enrollment__cohort", "project"
    ).all()
    serializer_class = ProjectAssignmentSerializer
    permission_classes = [ReadOnlyOrStaffOrTrainer]

    def get_queryset(self):
        queryset = super().get_queryset()
        for param, field in (
            ("enrollment", "enrollment_id"),
            ("project", "project_id"),
            ("cohort", "enrollment__cohort_id"),
        ):
            raw = self.request.query_params.get(param)
            if raw:
                try:
                    UUID(raw)
                except ValueError:
                    raise ValidationError({param: ["UUID invalide."]})
                queryset = queryset.filter(**{field: raw})
        return queryset


@extend_schema_view(
    list=extend_schema(summary="Lister les livrables soumis", tags=["Evaluations"]),
    create=extend_schema(summary="Soumettre un livrable de projet", tags=["Evaluations"]),
    retrieve=extend_schema(summary="Détail d'un livrable", tags=["Evaluations"]),
    update=extend_schema(summary="Modifier un livrable", tags=["Evaluations"]),
    partial_update=extend_schema(summary="Modifier partiellement un livrable", tags=["Evaluations"]),
    destroy=extend_schema(summary="Supprimer un livrable", tags=["Evaluations"]),
)
class DeliverableViewSet(viewsets.ModelViewSet):
    queryset = Deliverable.objects.select_related(
        "assignment__project", "assignment__enrollment__user", "reviewed_by"
    ).all()
    serializer_class = DeliverableSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        deliverable = serializer.save()
        deliverable.assignment.status = ProjectAssignment.StatusEnum.SUBMITTED
        deliverable.assignment.save(update_fields=["status", "updated_at"])

    @extend_schema(
        summary="Noter et valider/rejeter un livrable (Formateur/Admin)",
        request=GradeDeliverableSerializer,
        responses={200: DeliverableSerializer},
        tags=["Evaluations"],
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminOrOrganizerOrTrainer],
        url_path="grade",
    )
    def grade(self, request, pk=None):
        deliverable = self.get_object()
        serializer = GradeDeliverableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deliverable.mark_reviewed(
            reviewer=request.user,
            score=serializer.validated_data["score"],
            feedback=serializer.validated_data["feedback"],
            status_choice=serializer.validated_data["status"],
        )
        return Response(DeliverableSerializer(deliverable).data, status=status.HTTP_200_OK)
