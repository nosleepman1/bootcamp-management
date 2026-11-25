from django.urls import path

from .views import DashboardOverviewView, HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="api-health"),
    path("dashboard/stats/", DashboardOverviewView.as_view(), name="dashboard-stats"),
]
