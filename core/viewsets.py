from datetime import datetime, timedelta
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User, FriendRequest
from .serializers import FriendRequestSerializer, UserSerializer


class FriendRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer

    def list(self, request, *args, **kwargs):
        type = request.query_params.get("type")

        queryset = self.queryset.filter(status="pending")
        friend_requests = []
        if not type:
            friend_requests = queryset.filter(
                Q(to_user=request.user) | Q(from_user=request.user)
            )
        elif type == "received":
            friend_requests = queryset.filter(to_user=request.user)
        elif type == "sent":
            friend_requests = queryset.filter(from_user=request.user)

        serializer = FriendRequestSerializer(friend_requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def send_request(self, request):
        # Get data from request
        from_user = request.user
        to_user = request.data.get("to_user")

        # Check if user has sent 3 requests in last minute
        fr_req_in_last_min = FriendRequest.objects.filter(
            created_at__gte=(datetime.now() - timedelta(minutes=1))
        ).count()

        if fr_req_in_last_min >= 3:
            return Response(
                {"detail": "Friend Request limit reached. Try after sometime."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if to_user is provided
        if not to_user:
            return Response(
                {"detail": "to_user is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        if to_user == request.user.username:
            return Response(
                {"detail": "Request cant be sent to yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if to_user exists
        try:
            to_user = User.objects.get(username=to_user)
        except User.DoesNotExist:
            return Response(
                {"detail": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if friend request already exists
        if FriendRequest.objects.filter(from_user=from_user, to_user=to_user).exists():
            return Response(
                {"detail": "Friend request already sent."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create friend request
        friend_request = FriendRequest.objects.create(
            from_user=from_user, to_user=to_user, status="pending"
        )

        # Serialize and return response
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def accept_request(self, request, pk=None):
        # Get friend request
        try:
            friend_request = FriendRequest.objects.get(pk=pk)
        except FriendRequest.DoesNotExist:
            return Response(
                {"detail": "Friend request does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if request is for the authenticated user
        if friend_request.to_user != request.user:
            return Response(
                {"detail": "Unauthorized."}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Accept friend request
        friend_request.status = "accepted"
        friend_request.save()

        # Add Friend
        request.user.friends.add(friend_request.from_user)

        # Serialize and return response
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reject_request(self, request, pk=None):
        # Get friend request
        try:
            friend_request = FriendRequest.objects.get(pk=pk)
        except FriendRequest.DoesNotExist:
            return Response(
                {"detail": "Friend request does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if request is for the authenticated user
        if friend_request.to_user != request.user:
            return Response(
                {"detail": "Unauthorized."}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Reject friend request
        friend_request.status = "rejected"
        friend_request.save()

        # Serialize and return response
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel_request(self, request, pk=None):
        # Get friend request
        try:
            friend_request = FriendRequest.objects.get(pk=pk)
        except FriendRequest.DoesNotExist:
            return Response(
                {"detail": "Friend request does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if request is for the authenticated user
        if friend_request.from_user != request.user:
            return Response(
                {"detail": "Unauthorized."}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Reject friend request
        friend_request.delete()

        return HttpResponse(status=200)


class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def search(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response(
                {"detail": 'Query parameter "query" is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Search users by email
        email_exact_match = User.objects.filter(email=query).first()
        if email_exact_match:
            serializer = UserSerializer(email_exact_match)
            return Response(serializer.data)

        # Search users by name (case insensitive)
        name_partial_match = User.objects.filter(username__icontains=query)
        paginator = Paginator(name_partial_match, 10)  # Paginate results
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.page(page_number)
        total_users = paginator.count
        total_pages = paginator.num_pages

        serializer = UserSerializer(page_obj, many=True)
        response_data = {
            "results": serializer.data,
            "page_number": page_number,
            "total_users": total_users,
            "total_pages": total_pages,
        }
        return Response(response_data)

    @action(detail=False, methods=["get"])
    def friends(self, request):
        friends = request.user.friends.all()
        paginator = Paginator(friends, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.page(page_number)
        total_users = paginator.count
        total_pages = paginator.num_pages

        serializer = UserSerializer(page_obj, many=True)
        response_data = {
            "results": serializer.data,
            "page_number": page_number,
            "total_users": total_users,
            "total_pages": total_pages,
        }
        return Response(response_data)
