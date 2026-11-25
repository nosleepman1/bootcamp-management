from django.test import TestCase

from apps.certificates.models import Certificate
from apps.cohorts.tests.factories import CohortFactory, EnrollmentFactory
from apps.core.tests.base import API_PREFIX, AuthAPITestCase
from apps.core.tests.factories import UserFactory
from apps.users.models import User

CERTIFICATES_URL = f"{API_PREFIX}/certificates/"


class CertificateModelTests(TestCase):
    def test_certificate_is_created_with_default_values(self):
        certificate = Certificate.objects.create()

        self.assertIsNotNone(certificate.id)
        self.assertEqual(
            certificate.status,
            Certificate.StatusCertificateEnum.PENDING,
        )
        self.assertIsNotNone(certificate.date_generation)
        self.assertIsNone(certificate.date_envoi)
        self.assertEqual(certificate.file_path, "")
        self.assertIsNone(certificate.sent_by)

    def test_certificate_can_be_sent_by_an_admin(self):
        admin = User.objects.create_user(
            email="admin@example.com",
            password="test-password",
            role=User.Role.ADMIN,
        )

        certificate = Certificate.objects.create(
            status=Certificate.StatusCertificateEnum.SENT,
            sent_by=admin,
        )

        self.assertEqual(
            certificate.status,
            Certificate.StatusCertificateEnum.SENT,
        )
        self.assertEqual(certificate.sent_by, admin)

    def test_certificate_has_a_unique_uuid(self):
        certificate_1 = Certificate.objects.create()
        certificate_2 = Certificate.objects.create()

        self.assertNotEqual(certificate_1.id, certificate_2.id)


class CertificateApiTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.admin = UserFactory(admin=True)
        self.learner = UserFactory(first_name="Cheikh", last_name="Fall")
        self.cohort = CohortFactory(name="Cohorte Dakar Alpha")
        self.enrollment = EnrollmentFactory(cohort=self.cohort, user=self.learner)

    def test_admin_can_generate_and_send_certificate(self):
        res = self.auth(self.admin).post(
            CERTIFICATES_URL,
            {
                "enrollment": str(self.enrollment.id),
                "file_path": "certificates/cert-cheikh-fall.pdf",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        cert_id = res.data["id"]
        self.assertEqual(res.data["status"], Certificate.StatusCertificateEnum.PENDING)

        send_res = self.auth(self.admin).post(f"{CERTIFICATES_URL}{cert_id}/send/")
        self.assertEqual(send_res.status_code, 200)
        self.assertEqual(send_res.data["status"], Certificate.StatusCertificateEnum.SENT)
        self.assertIsNotNone(send_res.data["date_envoi"])
        self.assertEqual(send_res.data["sent_by"], self.admin.id)
