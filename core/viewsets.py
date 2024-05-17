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
    """
    Viewset for all APIs related to friend Requests
    """

    permission_classes = [IsAuthenticated]
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer

    def list(self, request, *args, **kwargs) -> Response:
        """
        List all friend requests.
        Filters by type if provided: 'received' or 'sent'.
        """

        # Get the type filter
        type: str = request.query_params.get("type")

        # We only need the friend requests which are pending
        queryset = self.queryset.filter(status="pending")

        friend_requests = []

        # If the filter is not specified we will fetch
        # All friend requests, whether sent or received
        if not type:
            friend_requests = queryset.filter(
                Q(to_user=request.user) | Q(from_user=request.user)
            )

        # Filter Received Requests
        elif type == "received":
            friend_requests = queryset.filter(to_user=request.user)

        # Filter Sent requests
        elif type == "sent":
            friend_requests = queryset.filter(from_user=request.user)

        # Serialize the response
        serializer = FriendRequestSerializer(friend_requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def send_request(self, request) -> Response:
        """
        Send friend request.
        Prevents sending to oneself and sending more than 3 requests in a minute.
        """

        # Get data from request
        from_user: User = request.user

        # User to whom the request is to be sent
        to_user: str = request.data.get("to_user")
        if not to_user:
            return Response(
                {"detail": "to_user is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Request cant be sent to oneself
        if to_user == request.user.username:
            return Response(
                {"detail": "Request cant be sent to yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user exists
        try:
            to_user: User = User.objects.get(username=to_user)
        except User.DoesNotExist:
            return Response(
                {"detail": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST
            )

        # find the number of requests sent in last minute
        fr_req_in_last_min: int = FriendRequest.objects.filter(
            created_at__gte=(datetime.now() - timedelta(minutes=1))
        ).count()

        # user can not send more than 3 requests in a min.
        if fr_req_in_last_min >= 3:
            return Response(
                {"detail": "Friend Request limit reached. Try after sometime."},
                status=status.HTTP_400_BAD_REQUEST,
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
    def accept_request(self, request, pk=None) -> Response:
        """
        Accept friend request.
        Adds friend and updates request status.
        """

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

        # Add the user as a Friend
        request.user.friends.add(friend_request.from_user)

        # Serialize and return response
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reject_request(self, request, pk=None) -> Response:
        """
        Reject friend request.
        Updates request status to 'rejected'.
        """

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
    def cancel_request(self, request, pk=None) -> Response:
        """
        Cancel friend request.
        Deletes the friend request.
        """

        # Get friend request
        try:
            friend_request = FriendRequest.objects.get(pk=pk)
        except FriendRequest.DoesNotExist:
            return Response(
                {"detail": "Friend request does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if request is sent by the authenticated user
        if friend_request.from_user != request.user:
            return Response(
                {"detail": "Unauthorized."}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Delete friend request
        friend_request.delete()

        return HttpResponse(status=200)


class UserViewSet(viewsets.ViewSet):
    """
    Viewset for all APIs related to Users
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def search(self, request) -> Response:
        """
        Search users by email or username.
        Returns paginated results with total users and pages.
        """
        # get the query given
        query: str = request.query_params.get("query")
        if not query:
            return Response(
                {"detail": 'Query parameter "query" is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Search users by email, this needs to be an exact search
        # Response wont be paginated
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
    def friends(self, request) -> Response:
        """
        List friends of the authenticated user.
        Returns paginated results with total users and pages.
        """
        # Fetch all the friends of a user
        friends = request.user.friends.all()

        # Response needs to be paginated
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
