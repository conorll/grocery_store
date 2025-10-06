from django.test import TestCase
from django.contrib.auth.models import User
from grocery_store_app.forms import CustomUserCreationForm


class CustomUserCreationFormTests(TestCase):
  def setUp(self):
    # Create an existing user for email validation tests
    self.existing_user = User.objects.create_user(
      username="existinguser",
      email="existing@example.com",
      password="password123"
    )

  def test_validate_email_pass(self):
    """Test that a unique email passes validation"""
    form_data = {
      'username': 'newuser',
      'first_name': 'John',
      'last_name': 'Doe',
      'email': 'new@example.com',
      'password1': 'testpassword123',
      'password2': 'testpassword123'
    }
    form = CustomUserCreationForm(data=form_data)
    self.assertTrue(form.is_valid())

  def test_validate_email_fail(self):
    """Test that a duplicate email fails validation"""
    form_data = {
      'username': 'newuser',
      'first_name': 'John',
      'last_name': 'Doe',
      'email': 'existing@example.com',  # This email already exists
      'password1': 'testpassword123',
      'password2': 'testpassword123'
    }
    form = CustomUserCreationForm(data=form_data)
    self.assertFalse(form.is_valid())
    self.assertIn('This email address is already registered.', form.errors['email'])

  def test_validate_name_pass(self):
    """Test that alphabetic names pass validation"""
    form_data = {
      'username': 'newuser',
      'first_name': 'John',
      'last_name': 'Doe',
      'email': 'valid@example.com',
      'password1': 'testpassword123',
      'password2': 'testpassword123'
    }
    form = CustomUserCreationForm(data=form_data)
    self.assertTrue(form.is_valid())

  def test_validate_name_fail(self):
    """Test that non-alphabetic names fail validation"""
    form_data = {
      'username': 'newuser',
      'first_name': 'John123',  # Contains numbers
      'last_name': 'Doe456',    # Contains numbers
      'email': 'valid@example.com',
      'password1': 'testpassword123',
      'password2': 'testpassword123'
    }
    form = CustomUserCreationForm(data=form_data)
    self.assertFalse(form.is_valid())
    self.assertIn('First name must contain only alphabetic characters.', form.errors['first_name'])
    self.assertIn('Last name must contain only alphabetic characters.', form.errors['last_name'])