from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import UserProfile
from .serializers import RegisterSerializer, UserProfileSerializer

# User registration
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email
        }, status=status.HTTP_201_CREATED)

# User profile view
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Return profile of the logged-in user
        return UserProfile.objects.get(user=self.request.user)