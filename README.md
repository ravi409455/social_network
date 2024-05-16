# Social Network
Simple Django based Social Network App

## APIs
- **SignUP**: Allows users to create a new account by providing a username, email, and password.
- **Login**: Enables users to authenticate themselves by providing their username and password.
- **Logout**: Allows authenticated users to log out of their account.
- **Search**: Users can search for other users using their email or username.
- **List Friend Requests**: Lists friend requests of a user and can filter by type (sent or received).
- **List Friends**: Lists friends who have accepted the request.
- **Send Friend Request**: Allows users to send friend requests, preventing sending to oneself, and restricting sending more than 3 requests in a minute.
- **Accept Friend Request**: Allows users to accept a friend request.
- **Reject Friend Request**: Allows users to reject a friend request.
- **Cancel Friend Request**: Allows users to cancel a friend request.

## Installation Steps
1. Pull the Docker image: `docker pull ghcr.io/ravi409455/social_network:local`
2. Run the Docker container: `docker run -p 8200:8000 -i ghcr.io/ravi409455/socialnetwork:local`

If you want to build the image locally: `docker build --tag ghcr.io/ravi409455/social_network:local .`

## Prerequisites
- Docker installed on your system.

For detailed API documentation with examples, visit [here](https://documenter.getpostman.com/view/4637220/2sA3JRafRZ#edad6647-80a0-473a-b874-c2a4f47ab55b)
