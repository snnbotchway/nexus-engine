"""URLs configuration for the Profile app."""
from rest_framework.routers import DefaultRouter

from .views import ProfileViewSet

router = DefaultRouter()
router.register("profiles", ProfileViewSet)

app_name = "profiles"

urlpatterns = router.urls
