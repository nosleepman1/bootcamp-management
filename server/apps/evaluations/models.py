from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel, UUIDModel


class ProjectAssignment(UUIDModel, TimeStampedModel):
    """Projet confié à un apprenant inscrit dans une cohorte."""

    class StatusEnum(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Submitted"
        VALIDATED = "validated", "Validated"
        NEEDS_REVISION = "needs_revision", "Needs Revision"

    enrollment = models.ForeignKey(
        "cohorts.Enrollment",
        on_delete=models.CASCADE,
        related_name="project_assignments",
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusEnum.choices,
        default=StatusEnum.ASSIGNED,
    )

    class Meta:
        db_table = "project_assignments"
        ordering = ["-created_at"]
        verbose_name = "Affectation de projet"
        verbose_name_plural = "Affectations de projets"
        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "project"],
                name="uniq_project_assignment_enrollment_project",
            )
        ]

    def clean(self):
        super().clean()
        if self.enrollment_id and self.project_id:
            if self.enrollment.cohort.program_id != self.project.program_id:
                raise ValidationError(
                    {"project": "Le projet assigné doit appartenir au programme de la cohorte de l'apprenant."}
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.enrollment_id} - {self.project.title} ({self.status})"


class Deliverable(UUIDModel, TimeStampedModel):
    """Soumission d'un livrable par l'apprenant et correction par un formateur."""

    class StatusEnum(models.TextChoices):
        PENDING_REVIEW = "pending_review", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    assignment = models.ForeignKey(
        ProjectAssignment,
        on_delete=models.CASCADE,
        related_name="deliverables",
    )
    repository_url = models.URLField(max_length=500)
    demo_url = models.URLField(max_length=500, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    feedback = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_deliverables",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusEnum.choices,
        default=StatusEnum.PENDING_REVIEW,
    )

    class Meta:
        db_table = "deliverables"
        ordering = ["-submitted_at"]
        verbose_name = "Livrable"
        verbose_name_plural = "Livrables"

    def mark_reviewed(self, reviewer, score, feedback, status_choice):
        self.reviewed_by = reviewer
        self.score = score
        self.feedback = feedback
        self.status = status_choice
        self.reviewed_at = timezone.now()
        self.save()
        if status_choice == self.StatusEnum.APPROVED:
            self.assignment.status = ProjectAssignment.StatusEnum.VALIDATED
        elif status_choice == self.StatusEnum.REJECTED:
            self.assignment.status = ProjectAssignment.StatusEnum.NEEDS_REVISION
        self.assignment.save()

    def __str__(self):
        return f"Livrable {self.id} ({self.status})"
