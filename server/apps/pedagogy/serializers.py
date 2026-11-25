from rest_framework import serializers

from .models import Absence, CourseSession


class CourseSessionSerializer(serializers.ModelSerializer):
    cohort_name = serializers.CharField(source="cohort.name", read_only=True)
    project_title = serializers.CharField(source="project.title", read_only=True)
    trainer_email = serializers.EmailField(source="trainer.email", read_only=True)
    absences_count = serializers.SerializerMethodField()

    class Meta:
        model = CourseSession
        fields = [
            "id",
            "cohort",
            "cohort_name",
            "project",
            "project_title",
            "trainer",
            "trainer_email",
            "title",
            "description",
            "session_date",
            "start_time",
            "end_time",
            "status",
            "absences_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "cohort_name",
            "project_title",
            "trainer_email",
            "absences_count",
            "created_at",
            "updated_at",
        ]

    def get_absences_count(self, obj):
        return obj.absences.filter(is_absent=True).count()

    def validate(self, attrs):
        cohort = attrs.get("cohort", getattr(self.instance, "cohort", None))
        project = attrs.get("project", getattr(self.instance, "project", None))
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))

        if cohort and project and project.program_id != cohort.program_id:
            raise serializers.ValidationError(
                {"project": "Le projet doit appartenir au même programme que la cohorte."}
            )
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError(
                {"end_time": "L'heure de fin doit être postérieure à l'heure de début."}
            )
        return attrs


class AbsenceSerializer(serializers.ModelSerializer):
    learner_email = serializers.EmailField(source="enrollment.user.email", read_only=True)
    learner_name = serializers.CharField(source="enrollment.user.full_name", read_only=True)
    session_title = serializers.CharField(source="course_session.title", read_only=True)

    class Meta:
        model = Absence
        fields = [
            "id",
            "course_session",
            "session_title",
            "enrollment",
            "learner_email",
            "learner_name",
            "is_absent",
            "is_justified",
            "reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "session_title",
            "learner_email",
            "learner_name",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        course_session = attrs.get(
            "course_session", getattr(self.instance, "course_session", None)
        )
        enrollment = attrs.get("enrollment", getattr(self.instance, "enrollment", None))
        if course_session and enrollment and enrollment.cohort_id != course_session.cohort_id:
            raise serializers.ValidationError(
                {"enrollment": "L'apprenant doit appartenir à la cohorte de la session pédagogique."}
            )
        return attrs
