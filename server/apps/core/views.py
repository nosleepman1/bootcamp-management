from django.db.models import Avg, Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.certificates.models import Certificate
from apps.cohorts.models import Cohort, Enrollment, Intake
from apps.evaluations.models import Deliverable, ProjectAssignment
from apps.pedagogy.models import Absence, CourseSession
from apps.programs.models import Program, Project
from apps.users.models import User


class HealthCheckView(APIView):
    """GET /api/v1/health/ — Endpoint public de supervision pour Docker / Kubernetes."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = []

    @extend_schema(
        summary="Vérifier l'état de santé de l'API",
        tags=["Core"],
    )
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": "academy-os-api",
                "version": "1.0.0",
            }
        )


class DashboardOverviewView(APIView):
    """GET /api/v1/dashboard/stats/ — Statistiques globales Academy OS."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Obtenir les KPIs globaux et métriques pédagogiques du dashboard",
        tags=["Core"],
    )
    def get(self, request):
        total_absences = Absence.objects.filter(is_absent=True).count()
        justified_absences = Absence.objects.filter(
            is_absent=True, is_justified=True
        ).count()
        avg_score = Deliverable.objects.filter(
            status=Deliverable.StatusEnum.APPROVED
        ).aggregate(avg=Avg("score"))["avg"]

        return Response(
            {
                "programs": {
                    "total": Program.objects.count(),
                    "active": Program.objects.filter(
                        status=Program.StatusProgramEnum.ACTIVE
                    ).count(),
                    "projects": Project.objects.count(),
                },
                "cohorts": {
                    "intakes": Intake.objects.count(),
                    "total": Cohort.objects.count(),
                    "ongoing": Cohort.objects.filter(
                        status=Cohort.StatusEnum.ONGOING
                    ).count(),
                    "enrollments": Enrollment.objects.filter(
                        status=Enrollment.StatusEnum.ACTIVE
                    ).count(),
                },
                "users": {
                    "total": User.objects.count(),
                    "learners": User.objects.filter(role=User.Role.LEARNER).count(),
                    "trainers": User.objects.filter(role=User.Role.TRAINER).count(),
                },
                "pedagogy": {
                    "course_sessions": CourseSession.objects.count(),
                    "total_absences": total_absences,
                    "justified_absences": justified_absences,
                },
                "evaluations": {
                    "assignments": ProjectAssignment.objects.count(),
                    "deliverables_submitted": Deliverable.objects.count(),
                    "average_approved_score": round(float(avg_score), 2)
                    if avg_score is not None
                    else None,
                },
                "certificates": {
                    "total": Certificate.objects.count(),
                    "sent": Certificate.objects.filter(
                        status=Certificate.StatusCertificateEnum.SENT
                    ).count(),
                },
            }
        )
