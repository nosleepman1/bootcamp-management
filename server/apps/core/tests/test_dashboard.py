from apps.core.tests.base import API_PREFIX, AuthAPITestCase
from apps.core.tests.factories import UserFactory
from apps.programs.tests.factories import ProgramFactory, ProjectFactory

HEALTH_URL = f"{API_PREFIX}/health/"
DASHBOARD_STATS_URL = f"{API_PREFIX}/dashboard/stats/"


class CoreDashboardAndHealthTests(AuthAPITestCase):
    def test_health_endpoint_is_public(self):
        response = self.client.get(HEALTH_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")

    def test_authenticated_user_can_fetch_dashboard_stats(self):
        admin = UserFactory(admin=True)
        program = ProgramFactory()
        ProjectFactory(program=program)

        response = self.auth(admin).get(DASHBOARD_STATS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["programs"]["total"], 1)
        self.assertEqual(response.data["programs"]["projects"], 1)
        self.assertIn("pedagogy", response.data)
        self.assertIn("evaluations", response.data)
        self.assertIn("certificates", response.data)
