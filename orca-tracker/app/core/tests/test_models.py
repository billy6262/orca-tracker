#tests for models

from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email.lower())
        self.assertTrue(user.check_password(password))

    def test_new_user_no_email(self):
        """Test creating a user without an email raises error."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('','Testpass123')

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser("test@example.com","Testpass123")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)