"""URLs configuration for the Profile app."""
from rest_framework.routers import DefaultRouter

from .views import FollowViewSet, ProfileViewSet

router = DefaultRouter()
router.register("profiles", ProfileViewSet)
router.register("follows", FollowViewSet)

app_name = "profiles"

urlpatterns = router.urls
