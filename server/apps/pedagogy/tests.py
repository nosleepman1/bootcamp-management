from datetime import date

from apps.cohorts.tests.factories import CohortFactory, EnrollmentFactory
from apps.core.tests.base import API_PREFIX, AuthAPITestCase
from apps.core.tests.factories import UserFactory
from apps.pedagogy.models import Absence, CourseSession
from apps.programs.tests.factories import ProgramFactory, ProjectFactory

SESSIONS_URL = f"{API_PREFIX}/pedagogy/sessions/"
ABSENCES_URL = f"{API_PREFIX}/pedagogy/absences/"


class PedagogyApiTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.admin = UserFactory(admin=True)
        self.trainer = UserFactory(trainer=True)
        self.learner = UserFactory(first_name="Moussa", last_name="Diop")
        self.program = ProgramFactory(title="Développement Web")
        self.project = ProjectFactory(program=self.program, title="SaaS E-learning")
        self.cohort = CohortFactory(program=self.program, name="Cohorte Baol 1")
        self.enrollment = EnrollmentFactory(cohort=self.cohort, user=self.learner)

    def test_trainer_can_create_course_session_for_cohort_project(self):
        payload = {
            "cohort": str(self.cohort.id),
            "project": str(self.project.id),
            "title": "Architecture REST & Authentification JWT",
            "description": "Introduction aux bonnes pratiques DRF.",
            "session_date": "2026-03-10",
            "start_time": "09:00:00",
            "end_time": "12:30:00",
            "status": "scheduled",
        }
        response = self.auth(self.trainer).post(SESSIONS_URL, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["trainer_email"], self.trainer.email)
        self.assertEqual(response.data["project_title"], "SaaS E-learning")

    def test_cannot_create_session_with_project_from_another_program(self):
        other_program = ProgramFactory(title="Cybersécurité")
        other_project = ProjectFactory(program=other_program, title="Pentest Réseau")
        payload = {
            "cohort": str(self.cohort.id),
            "project": str(other_project.id),
            "title": "Cours invalide",
            "session_date": "2026-03-10",
        }
        response = self.auth(self.trainer).post(SESSIONS_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("project", response.data)

    def test_record_and_justify_learner_absence(self):
        session = CourseSession.objects.create(
            cohort=self.cohort,
            project=self.project,
            trainer=self.trainer,
            title="Hooks React & TanStack Query",
            session_date=date(2026, 3, 12),
        )
        payload = {
            "course_session": str(session.id),
            "enrollment": str(self.enrollment.id),
            "is_absent": True,
            "is_justified": False,
            "reason": "Problème de transport",
        }
        res = self.auth(self.trainer).post(ABSENCES_URL, payload, format="json")
        self.assertEqual(res.status_code, 201)
        absence_id = res.data["id"]

        # Justify absence
        patch_res = self.auth(self.admin).patch(
            f"{ABSENCES_URL}{absence_id}/",
            {"is_justified": True, "reason": "Certificat médical fourni"},
            format="json",
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertTrue(patch_res.data["is_justified"])

        # Filter absences by cohort
        list_res = self.auth(self.learner).get(f"{ABSENCES_URL}?cohort={self.cohort.id}")
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(list_res.data["count"], 1)

    def test_cannot_record_absence_for_enrollment_outside_session_cohort(self):
        other_cohort = CohortFactory(program=self.program)
        other_enrollment = EnrollmentFactory(cohort=other_cohort)
        session = CourseSession.objects.create(
            cohort=self.cohort,
            project=self.project,
            trainer=self.trainer,
            title="Docker & CI/CD",
            session_date=date(2026, 3, 15),
        )
        res = self.auth(self.trainer).post(
            ABSENCES_URL,
            {
                "course_session": str(session.id),
                "enrollment": str(other_enrollment.id),
                "is_absent": True,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("enrollment", res.data)
