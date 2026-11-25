from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProgramViewSet, ProjectViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"", ProgramViewSet, basename="program")

urlpatterns = [
    path("", include(router.urls)),
]
