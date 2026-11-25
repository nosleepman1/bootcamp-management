from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class CourseSession(UUIDModel, TimeStampedModel):
    """Session pédagogique (cours dispensé par un formateur à une cohorte autour d'un projet)."""

    class StatusEnum(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    cohort = models.ForeignKey(
        "cohorts.Cohort",
        on_delete=models.CASCADE,
        related_name="course_sessions",
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="course_sessions",
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="taught_sessions",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    session_date = models.DateField()
    start_time = models.TimeField(default="09:00")
    end_time = models.TimeField(default="12:00")
    status = models.CharField(
        max_length=20,
        choices=StatusEnum.choices,
        default=StatusEnum.SCHEDULED,
    )

    class Meta:
        db_table = "course_sessions"
        ordering = ["-session_date", "-start_time"]
        verbose_name = "Session pédagogique"
        verbose_name_plural = "Sessions pédagogiques"

    def clean(self):
        super().clean()
        if self.cohort_id and self.project_id:
            if self.project.program_id != self.cohort.program_id:
                raise ValidationError(
                    {"project": "Le projet doit appartenir au même programme que la cohorte."}
                )
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError(
                {"end_time": "L'heure de fin doit être postérieure à l'heure de début."}
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.session_date})"


class Absence(UUIDModel, TimeStampedModel):
    """Absence ou présence relevée pour un apprenant inscrit lors d'une session pédagogique."""

    course_session = models.ForeignKey(
        CourseSession,
        on_delete=models.CASCADE,
        related_name="absences",
    )
    enrollment = models.ForeignKey(
        "cohorts.Enrollment",
        on_delete=models.CASCADE,
        related_name="absences",
    )
    is_absent = models.BooleanField(default=True)
    is_justified = models.BooleanField(default=False)
    reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "pedagogy_absences"
        ordering = ["-created_at"]
        verbose_name = "Absence"
        verbose_name_plural = "Absences"
        constraints = [
            models.UniqueConstraint(
                fields=["course_session", "enrollment"],
                name="uniq_absence_session_enrollment",
            )
        ]

    def clean(self):
        super().clean()
        if self.course_session_id and self.enrollment_id:
            if self.enrollment.cohort_id != self.course_session.cohort_id:
                raise ValidationError(
                    {"enrollment": "L'apprenant doit appartenir à la cohorte de la session pédagogique."}
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        state = "Absent" if self.is_absent else "Présent"
        return f"{self.enrollment_id} - {self.course_session_id} ({state})"
