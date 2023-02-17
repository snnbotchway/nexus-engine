"""Views for the Profiles app."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Profile
from .serializers import (
    ProfileImageSerializer,
    ProfileSerializer,
    UserReadOnlyProfileSerializer,
)


class ProfileViewSet(ModelViewSet):
    """The Profile view set."""

    http_method_names = [
        "delete",
        "get",
        "head",
        "options",
        "patch",
        "post",
    ]

    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        """Return appropriate serializer considering the request method."""
        serializer_classes = {
            "PATCH": UserReadOnlyProfileSerializer,
            "me": UserReadOnlyProfileSerializer,
            "upload_image": ProfileImageSerializer,
            "admin_upload_image": ProfileImageSerializer,
        }
        method = self.request.method
        action = self.action
        serializer_class = self.serializer_class

        if method in serializer_classes:
            serializer_class = serializer_classes[method]
        elif action in serializer_classes:
            serializer_class = serializer_classes[action]

        return serializer_class

    @action(
        detail=False,
        methods=["GET", "PATCH", "POST", "DELETE"],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Me action to manage current user's profile."""
        if request.method == "POST":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "GET":
            profile, _ = Profile.objects.get_or_create(user=request.user)
            serializer = self.get_serializer(profile, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PATCH":
            profile, _ = Profile.objects.get_or_create(user=request.user)
            serializer = self.get_serializer(profile, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            profile = get_object_or_404(Profile, user=request.user)
            profile.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["POST"],
        detail=False,
        url_path="upload-image",
        permission_classes=[IsAuthenticated],
    )
    def upload_image(self, request, pk=None):
        """Upload an image to current user's profile."""
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def admin_upload_image(self, request, pk=None):
        """Upload an image to any profile."""
        profile, _ = Profile.objects.get_or_create(pk=pk)
        serializer = self.get_serializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
