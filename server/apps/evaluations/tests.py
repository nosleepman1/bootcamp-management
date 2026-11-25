from apps.cohorts.tests.factories import CohortFactory, EnrollmentFactory
from apps.core.tests.base import API_PREFIX, AuthAPITestCase
from apps.core.tests.factories import UserFactory
from apps.evaluations.models import Deliverable, ProjectAssignment
from apps.programs.tests.factories import ProgramFactory, ProjectFactory

ASSIGNMENTS_URL = f"{API_PREFIX}/evaluations/assignments/"
DELIVERABLES_URL = f"{API_PREFIX}/evaluations/deliverables/"


class EvaluationsWorkflowTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.admin = UserFactory(admin=True)
        self.trainer = UserFactory(trainer=True)
        self.learner = UserFactory(first_name="Awa", last_name="Sow")
        self.program = ProgramFactory(title="Data & IA")
        self.project = ProjectFactory(program=self.program, title="Pipeline ML")
        self.cohort = CohortFactory(program=self.program, name="Cohorte IA 1")
        self.enrollment = EnrollmentFactory(cohort=self.cohort, user=self.learner)

    def test_trainer_can_assign_project_and_learner_can_submit_deliverable_and_trainer_grades(self):
        assign_res = self.auth(self.trainer).post(
            ASSIGNMENTS_URL,
            {
                "enrollment": str(self.enrollment.id),
                "project": str(self.project.id),
                "due_date": "2026-06-30",
            },
            format="json",
        )
        self.assertEqual(assign_res.status_code, 201)
        assignment_id = assign_res.data["id"]

        # Learner submits deliverable
        submit_res = self.auth(self.learner).post(
            DELIVERABLES_URL,
            {
                "assignment": assignment_id,
                "repository_url": "https://github.com/nosleepman1/bootcamp-management",
                "demo_url": "https://demo.xarala.co",
                "notes": "Implémentation complète avec tests.",
            },
            format="json",
        )
        self.assertEqual(submit_res.status_code, 201)
        deliverable_id = submit_res.data["id"]

        assignment = ProjectAssignment.objects.get(id=assignment_id)
        self.assertEqual(assignment.status, ProjectAssignment.StatusEnum.SUBMITTED)

        # Trainer grades deliverable
        grade_res = self.auth(self.trainer).post(
            f"{DELIVERABLES_URL}{deliverable_id}/grade/",
            {
                "score": "94.50",
                "feedback": "Excellent travail, architecture très propre.",
                "status": Deliverable.StatusEnum.APPROVED,
            },
            format="json",
        )
        self.assertEqual(grade_res.status_code, 200)
        self.assertEqual(grade_res.data["status"], Deliverable.StatusEnum.APPROVED)
        self.assertEqual(grade_res.data["reviewer_email"], self.trainer.email)

        assignment.refresh_from_db()
        self.assertEqual(assignment.status, ProjectAssignment.StatusEnum.VALIDATED)

    def test_cannot_assign_project_from_different_program(self):
        other_program = ProgramFactory(title="Design UI/UX")
        other_project = ProjectFactory(program=other_program, title="Design System Figma")
        res = self.auth(self.trainer).post(
            ASSIGNMENTS_URL,
            {
                "enrollment": str(self.enrollment.id),
                "project": str(other_project.id),
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("project", res.data)
