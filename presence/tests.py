# core/tests.py

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import Department, UserProfile, LoginAttempt, UserSession, PasswordReset, LogEntry
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
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
        
class SecurityAuditAPITests(TestCase):
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
        # Création d'une session utilisateur
        self.user_session = UserSession.objects.create(
            user=self.regular_user,
            session_key='abc123',
            ip_address='127.0.0.1',
            user_agent='TestAgent/1.0',
            last_activity='2024-04-27T12:00:00Z',
            is_active=True
        )
        # Création d'une tentative de connexion
        self.login_attempt = LoginAttempt.objects.create(
            user=self.regular_user,
            ip_address='127.0.0.1',
            success=True,
            user_agent='TestAgent/1.0'
        )
        # Création d'un log d'opération
        self.log_entry = LogEntry.objects.create(
            user=self.admin_user,
            action='Création de département',
            ip_address='127.0.0.1',
            user_agent='AdminAgent/1.0'
        )
        # Création d'une demande de réinitialisation de mot de passe
        self.password_reset = PasswordReset.objects.create(
            user=self.regular_user,
            token='securetoken123',
            used=False,
            ip_address='127.0.0.1'
        )

    def authenticate(self, user):
        """
        Fonction d'authentification pour obtenir un token JWT.
        """
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    # Tests pour LoginAttemptViewSet
    def test_admin_can_view_login_attempts(self):
        self.authenticate(self.admin_user)
        url = reverse('loginattempt-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.regular_user.id)

    def test_regular_user_cannot_view_login_attempts(self):
        self.authenticate(self.regular_user)
        url = reverse('loginattempt-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Tests pour UserSessionViewSet
    def test_admin_can_view_user_sessions(self):
        self.authenticate(self.admin_user)
        url = reverse('usersession-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.regular_user.id)

    def test_regular_user_cannot_view_user_sessions(self):
        self.authenticate(self.regular_user)
        url = reverse('usersession-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_terminate_user_session(self):
        self.authenticate(self.admin_user)
        url = reverse('usersession-terminate', args=[self.user_session.id])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_session.refresh_from_db()
        self.assertFalse(self.user_session.is_active)

    def test_regular_user_cannot_terminate_user_session(self):
        self.authenticate(self.regular_user)
        url = reverse('usersession-terminate', args=[self.user_session.id])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Tests pour PasswordResetViewSet
    def test_admin_can_view_password_resets(self):
        self.authenticate(self.admin_user)
        url = reverse('passwordreset-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.regular_user.id)

    def test_regular_user_cannot_view_password_resets(self):
        self.authenticate(self.regular_user)
        url = reverse('passwordreset-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_password_reset(self):
        self.authenticate(self.admin_user)
        url = reverse('passwordreset-list')
        data = {
            'user': self.regular_user.id,
            'token': 'newtoken456',
            'used': False,
            'ip_address': '192.168.1.1'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PasswordReset.objects.count(), 2)
        self.assertEqual(PasswordReset.objects.get(id=response.data['id']).token, 'newtoken456')

    def test_regular_user_cannot_create_password_reset(self):
        self.authenticate(self.regular_user)
        url = reverse('passwordreset-list')
        data = {
            'user': self.regular_user.id,
            'token': 'anothertoken789',
            'used': False,
            'ip_address': '192.168.1.2'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Tests pour LogEntryViewSet
    def test_admin_can_view_log_entries(self):
        self.authenticate(self.admin_user)
        url = reverse('logentry-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['action'], 'Création de département')

    def test_regular_user_cannot_view_log_entries(self):
        self.authenticate(self.regular_user)
        url = reverse('logentry-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Tests supplémentaires pour sécurité et audit
    def test_password_reset_token_unique(self):
        self.authenticate(self.admin_user)
        url = reverse('passwordreset-list')
        data = {
            'user': self.regular_user.id,
            'token': 'unique_token_123',
            'used': False,
            'ip_address': '10.0.0.1'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Tenter de créer un autre avec le même token
        data_duplicate = {
            'user': self.regular_user.id,
            'token': 'unique_token_123',
            'used': False,
            'ip_address': '10.0.0.2'
        }
        response_duplicate = self.client.post(url, data_duplicate, format='json')
        self.assertEqual(response_duplicate.status_code, status.HTTP_400_BAD_REQUEST)

    def test_log_entry_creation_on_action(self):
        # Simuler la création d'un log entry via une action
        # Ici, nous avons déjà créé un log entry dans setUp
        self.authenticate(self.admin_user)
        url = reverse('logentry-list')
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['action'], 'Création de département')

    def test_login_attempt_creation(self):
        # Simuler une tentative de connexion
        # Ceci devrait être géré automatiquement via des signaux ou des middlewares
        # Pour le test, nous allons créer manuellement une tentative
        LoginAttempt.objects.create(
            user=self.regular_user,
            ip_address='127.0.0.1',
            success=False,
            user_agent='TestAgent/2.0'
        )
        self.authenticate(self.admin_user)
        url = reverse('loginattempt-list')
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 2)  # Initial dans setUp + nouvelle tentative

    def test_user_session_last_activity_update(self):
        # Mettre à jour l'activité d'une session et vérifier
        self.authenticate(self.admin_user)
        url = reverse('usersession-detail', args=[self.user_session.id])
        data = {
            'last_activity': '2024-04-27T13:00:00Z'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_session.refresh_from_db()
        self.assertEqual(str(self.user_session.last_activity), '2024-04-27T13:00:00Z')
