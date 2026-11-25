from rest_framework import serializers

from .models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    learner_email = serializers.EmailField(
        source="enrollment.user.email", read_only=True, default=None
    )
    learner_name = serializers.CharField(
        source="enrollment.user.full_name", read_only=True, default=""
    )
    cohort_name = serializers.CharField(
        source="enrollment.cohort.name", read_only=True, default=""
    )

    class Meta:
        model = Certificate
        fields = [
            "id",
            "enrollment",
            "learner_email",
            "learner_name",
            "cohort_name",
            "date_generation",
            "date_envoi",
            "file_path",
            "status",
            "sent_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "learner_email",
            "learner_name",
            "cohort_name",
            "date_generation",
            "date_envoi",
            "sent_by",
            "created_at",
            "updated_at",
        ]
