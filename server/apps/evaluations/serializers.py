from rest_framework import serializers

from .models import Deliverable, ProjectAssignment


class ProjectAssignmentSerializer(serializers.ModelSerializer):
    learner_email = serializers.EmailField(source="enrollment.user.email", read_only=True)
    learner_name = serializers.CharField(source="enrollment.user.full_name", read_only=True)
    project_title = serializers.CharField(source="project.title", read_only=True)
    cohort_id = serializers.UUIDField(source="enrollment.cohort_id", read_only=True)

    class Meta:
        model = ProjectAssignment
        fields = [
            "id",
            "enrollment",
            "cohort_id",
            "learner_email",
            "learner_name",
            "project",
            "project_title",
            "due_date",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "cohort_id",
            "learner_email",
            "learner_name",
            "project_title",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        enrollment = attrs.get("enrollment", getattr(self.instance, "enrollment", None))
        project = attrs.get("project", getattr(self.instance, "project", None))
        if enrollment and project and enrollment.cohort.program_id != project.program_id:
            raise serializers.ValidationError(
                {"project": "Le projet assigné doit appartenir au programme de la cohorte de l'apprenant."}
            )
        return attrs


class DeliverableSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="assignment.project.title", read_only=True)
    learner_email = serializers.EmailField(
        source="assignment.enrollment.user.email", read_only=True
    )
    reviewer_email = serializers.EmailField(source="reviewed_by.email", read_only=True)

    class Meta:
        model = Deliverable
        fields = [
            "id",
            "assignment",
            "project_title",
            "learner_email",
            "repository_url",
            "demo_url",
            "notes",
            "submitted_at",
            "score",
            "feedback",
            "reviewed_by",
            "reviewer_email",
            "reviewed_at",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "project_title",
            "learner_email",
            "submitted_at",
            "reviewed_by",
            "reviewer_email",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]


class GradeDeliverableSerializer(serializers.Serializer):
    score = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=100)
    feedback = serializers.CharField(required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(
        choices=[
            Deliverable.StatusEnum.APPROVED,
            Deliverable.StatusEnum.REJECTED,
        ]
    )
