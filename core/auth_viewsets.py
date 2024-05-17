from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from django.contrib.auth import login, authenticate, logout
from .models import User as User
from .serializers import LoginSerializer, SignupSerializer


class UserAuthViewSet(ViewSet):
    """
    Viewset to handle user authentication related APIS
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return Response({"detail": "Login successful."})
            else:
                return Response(
                    {"detail": "Invalid username or password."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def signup(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            _ = User.objects.create_user(
                username=serializer.validated_data["username"],
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
            return Response({"detail": "Signup successful."})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        authentication_classes=[BasicAuthentication],
    )
    def logout(self, request):
        logout(request)
        return Response({"detail": "Logout successful."})
