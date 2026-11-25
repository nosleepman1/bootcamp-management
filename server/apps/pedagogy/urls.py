from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AbsenceViewSet, CourseSessionViewSet

router = DefaultRouter()
router.register(r"sessions", CourseSessionViewSet, basename="course-session")
router.register(r"absences", AbsenceViewSet, basename="absence")

urlpatterns = [
    path("pedagogy/", include(router.urls)),
]
