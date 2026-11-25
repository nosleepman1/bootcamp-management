from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DeliverableViewSet, ProjectAssignmentViewSet

router = DefaultRouter()
router.register(r"assignments", ProjectAssignmentViewSet, basename="project-assignment")
router.register(r"deliverables", DeliverableViewSet, basename="deliverable")

urlpatterns = [
    path("evaluations/", include(router.urls)),
]
