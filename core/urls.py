from rest_framework.routers import DefaultRouter
from .auth_viewsets import UserAuthViewSet
from .viewsets import FriendRequestViewSet, UserViewSet

router = DefaultRouter()
router.register("auth", UserAuthViewSet, basename="auth")
router.register("friend", FriendRequestViewSet, basename="friend")
router.register("user", UserViewSet, basename="user")


urlpatterns = router.urls
