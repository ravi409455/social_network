from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Attributes
    ----------
    username : str
        The username of the user.
    email : str
        The email address of the user. It must be unique.
    friends : ManyToManyField
        A relationship field representing the friends of the user.
    """

    email = models.EmailField(unique=True)
    friends = models.ManyToManyField("self", symmetrical=True, blank=True)


class FriendRequest(models.Model):
    """
    Attributes
    ----------
    from_user : ForeignKey
        The user who sent the friend request.
    to_user : ForeignKey
        The user who received the friend request.
    status : str
        The status of the friend request. It can be "pending", "accepted", or "rejected".
    created_at : DateTimeField
        The timestamp indicating when the friend request was created.
    """

    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_requests"
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_requests"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.from_user}->{self.to_user}"
