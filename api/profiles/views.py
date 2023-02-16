"""Views for the Profiles app."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Profile
from .serializers import ProfileSerializer, UserReadOnlyProfileSerializer


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

    queryset = Profile.objects.select_related("user").all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        """Return appropriate serializer considering the request method."""
        if self.request.method == "PATCH":
            return UserReadOnlyProfileSerializer
        return ProfileSerializer

    @action(
        detail=False,
        methods=["GET", "PATCH", "POST", "DELETE"],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Me action to manage current user's profile."""
        if request.method == "POST":
            serializer = UserReadOnlyProfileSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user_id=request.user.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "GET":
            profile, _ = Profile.objects.get_or_create(user_id=request.user.id)
            serializer = ProfileSerializer(profile, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PATCH":
            profile, _ = Profile.objects.get_or_create(user_id=request.user.id)
            serializer = UserReadOnlyProfileSerializer(profile, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            profile = get_object_or_404(Profile, user_id=request.user.id)
            profile.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
