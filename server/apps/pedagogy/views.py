from uuid import UUID

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.users.permissions import ReadOnlyOrHasRole
from .models import Absence, CourseSession
from .serializers import AbsenceSerializer, CourseSessionSerializer


class ReadOnlyOrStaffOrTrainer(ReadOnlyOrHasRole):
    allowed_roles = ("admin", "organizer", "trainer")


@extend_schema_view(
    list=extend_schema(summary="Lister les sessions pédagogiques", tags=["Pedagogy"]),
    create=extend_schema(summary="Créer une session pédagogique", tags=["Pedagogy"]),
    retrieve=extend_schema(summary="Détail d'une session pédagogique", tags=["Pedagogy"]),
    update=extend_schema(summary="Modifier une session pédagogique", tags=["Pedagogy"]),
    partial_update=extend_schema(summary="Modifier partiellement une session", tags=["Pedagogy"]),
    destroy=extend_schema(summary="Supprimer une session pédagogique", tags=["Pedagogy"]),
)
class CourseSessionViewSet(viewsets.ModelViewSet):
    """CRUD des sessions pédagogiques (cours liés à une cohorte et un projet)."""

    queryset = CourseSession.objects.select_related("cohort", "project", "trainer").all()
    serializer_class = CourseSessionSerializer
    permission_classes = [ReadOnlyOrStaffOrTrainer]

    def get_queryset(self):
        queryset = super().get_queryset()
        for param, field in (("cohort", "cohort_id"), ("project", "project_id")):
            raw = self.request.query_params.get(param)
            if raw:
                try:
                    UUID(raw)
                except ValueError:
                    raise ValidationError({param: ["UUID invalide."]})
                queryset = queryset.filter(**{field: raw})
        return queryset

    def perform_create(self, serializer):
        trainer = serializer.validated_data.get("trainer")
        if not trainer and self.request.user.role == "trainer":
            serializer.save(trainer=self.request.user)
        else:
            serializer.save()


@extend_schema_view(
    list=extend_schema(summary="Lister les présences et absences", tags=["Pedagogy"]),
    create=extend_schema(summary="Enregistrer une présence ou absence", tags=["Pedagogy"]),
    retrieve=extend_schema(summary="Détail d'un relevé d'absence", tags=["Pedagogy"]),
    update=extend_schema(summary="Modifier un relevé d'absence", tags=["Pedagogy"]),
    partial_update=extend_schema(summary="Justifier ou modifier une absence", tags=["Pedagogy"]),
    destroy=extend_schema(summary="Supprimer un relevé d'absence", tags=["Pedagogy"]),
)
class AbsenceViewSet(viewsets.ModelViewSet):
    """CRUD du suivi des présences et absences par session pédagogique."""

    queryset = Absence.objects.select_related(
        "course_session", "enrollment__user"
    ).all()
    serializer_class = AbsenceSerializer
    permission_classes = [ReadOnlyOrStaffOrTrainer]

    def get_queryset(self):
        queryset = super().get_queryset()
        for param, field in (
            ("course_session", "course_session_id"),
            ("enrollment", "enrollment_id"),
            ("cohort", "course_session__cohort_id"),
        ):
            raw = self.request.query_params.get(param)
            if raw:
                try:
                    UUID(raw)
                except ValueError:
                    raise ValidationError({param: ["UUID invalide."]})
                queryset = queryset.filter(**{field: raw})
        return queryset
