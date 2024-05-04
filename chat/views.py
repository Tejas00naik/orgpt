from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from chat.serializers import UserSerializer

# Create your views here.

class RegistrationView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Simulate event to frontend to load the first chat page
            return Response({
                'message': 'Registration successful. Redirecting to chat page...',
                'userId': user.id  # or any other user identifier or token
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
