from rest_framework import serializers
from .models import User, FriendRequest


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """

    class Meta:
        model = User
        fields = ["id", "username", "email"]


class FriendRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for FriendRequest model.
    """

    from_user = serializers.StringRelatedField()
    to_user = serializers.StringRelatedField()

    class Meta:
        model = FriendRequest
        fields = ["id", "from_user", "to_user", "status", "created_at"]


class LoginSerializer(serializers.Serializer):
    """
    Use this serializer to validate user login credentials.
    """

    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            raise serializers.ValidationError("Must include 'username' and 'password'.")

        return data


class SignupSerializer(serializers.Serializer):
    """
    Use this serializer to validate user signup data.
    """

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )
        return value

    def validate(self, data):
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email is already in use.")

        if not username:
            raise serializers.ValidationError("Username is required.")

        if not email:
            raise serializers.ValidationError("Email is required.")

        if not password:
            raise serializers.ValidationError("Password is required.")

        return data
