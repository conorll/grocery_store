from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class UserManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_login_html_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_signup_html_loads(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign Up')
        self.assertTemplateUsed(response, 'registration/signup.html')

    def test_profile_html_loads(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Profile')
        self.assertTemplateUsed(response, 'grocery_store_app/profile.html')

    def test_edit_profile_html_loads(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Personal Details')
        self.assertTemplateUsed(response, 'grocery_store_app/edit_profile.html')
