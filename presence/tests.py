# core/tests.py

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import Department, UserProfile
from rest_framework import status
from django.urls import reverse

class UserProfileAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Création d'un utilisateur admin
        self.admin_user = User.objects.create_superuser(
            username='admin', 
            email='admin@example.com', 
            password='adminpass'
        )
        # Création d'un utilisateur régulier
        self.regular_user = User.objects.create_user(
            username='user1', 
            email='user1@example.com', 
            password='userpass'
        )
        # Création d'un département
        self.department = Department.objects.create(
            name='IT', 
            code='IT01', 
            manager=self.admin_user
        )
        # Création des profils utilisateurs
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user, 
            matricule='BG20230001', 
            department=self.department, 
            role='ADMIN'
        )
        self.regular_profile = UserProfile.objects.create(
            user=self.regular_user, 
            matricule='BG20230002', 
            department=self.department, 
            role='STAFF'
        )

    def authenticate(self, user):
        """
        Fonction d'authentification pour obtenir un token JWT.
        """
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': user.username, 'password': 'adminpass' if user.is_superuser else 'userpass'}, format='json')
        token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_admin_can_create_department(self):
        self.authenticate(self.admin_user)
        url = reverse('department-list')
        data = {
            'name': 'HR',
            'code': 'HR01',
            'description': 'Human Resources',
            'manager': self.admin_user.id,
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Department.objects.count(), 2)
        self.assertEqual(Department.objects.get(code='HR01').name, 'HR')

    def test_regular_user_cannot_create_department(self):
        self.authenticate(self.regular_user)
        url = reverse('department-list')
        data = {
            'name': 'HR',
            'code': 'HR01',
            'description': 'Human Resources',
            'manager': self.admin_user.id,
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_departments(self):
        # Authentifier en tant qu'utilisateur régulier
        self.authenticate(self.regular_user)
        url = reverse('department-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'IT')

    def test_admin_can_create_user(self):
        self.authenticate(self.admin_user)
        url = reverse('user-list')
        data = {
            'username': 'user2',
            'password': 'user2pass',
            'password2': 'user2pass',
            'email': 'user2@example.com',
            'first_name': 'User',
            'last_name': 'Deux'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        new_user = User.objects.get(username='user2')
        self.assertEqual(new_user.email, 'user2@example.com')

    def test_regular_user_cannot_create_user(self):
        self.authenticate(self.regular_user)
        url = reverse('user-list')
        data = {
            'username': 'user3',
            'password': 'user3pass',
            'password2': 'user3pass',
            'email': 'user3@example.com',
            'first_name': 'User',
            'last_name': 'Trois'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_users(self):
        self.authenticate(self.admin_user)
        url = reverse('user-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_regular_user_cannot_view_users(self):
        self.authenticate(self.regular_user)
        url = reverse('user-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_view_own_profile(self):
        self.authenticate(self.regular_user)
        url = reverse('user-profile', args=[self.regular_user.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['matricule'], 'BG20230002')

    def test_user_cannot_view_other_profiles(self):
        self.authenticate(self.regular_user)
        url = reverse('user-profile', args=[self.admin_user.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_update_own_profile(self):
        self.authenticate(self.regular_user)
        url = reverse('user-profile', args=[self.regular_user.id])
        data = {
            'phone_number': '1234567890',
            'address': '123 Main St',
            'emergency_contact': 'John Doe',
            'emergency_phone': '0987654321',
            'role': 'SECURITY',  # Exemple de mise à jour du rôle
            'department_id': self.department.id
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_profile.refresh_from_db()
        self.assertEqual(self.regular_profile.phone_number, '1234567890')
        self.assertEqual(self.regular_profile.emergency_phone, '0987654321')
        self.assertEqual(self.regular_profile.role, 'SECURITY')

    def test_user_cannot_update_other_profile(self):
        self.authenticate(self.regular_user)
        url = reverse('user-profile', args=[self.admin_user.id])
        data = {
            'phone_number': '1234567890'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authentication_with_jwt(self):
        # Tester l'obtention du token JWT
        url = reverse('token_obtain_pair')
        data = {'username': 'user1', 'password': 'userpass'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_access_protected_endpoint_with_token(self):
        # Obtenir un token JWT
        url = reverse('token_obtain_pair')
        data = {'username': 'user1', 'password': 'userpass'}
        response = self.client.post(url, data, format='json')
        token = response.data.get('access')

        # Accéder à un endpoint protégé
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url = reverse('department-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_endpoint_without_token(self):
        # Tenter d'accéder à un endpoint protégé sans token
        url = reverse('department-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
