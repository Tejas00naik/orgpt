from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

class RegistrationTestCase(APITestCase):
    def test_registration_success(self):
        url = reverse('register')  # Make sure to have the correct URL name for registration
        data = {
            'username': 'newuser',
            'email': 'user@example.com',
            'password': 'securepassword123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('userId', response.data)

    def test_registration_failure_on_blank_email(self):
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': '',  # Blank email
            'password': 'securepassword123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_failure_on_duplicate_username(self):
        User.objects.create_user(username='newuser', email='user@example.com', password='securepassword123')
        url = reverse('register')
        data = {
            'username': 'newuser',  # Duplicate username
            'email': 'user2@example.com',
            'password': 'securepassword123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
