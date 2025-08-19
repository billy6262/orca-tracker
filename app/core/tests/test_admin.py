"""
tests the admindashboard functionality
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client

class AdminSiteTests(TestCase):
    """Test admin dashboard."""

    def setUp(self):
        """Set up dummy  user and client."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email="reguser@example.com",
            password="userpass123",
            )
        
    def test_users_listed(self):
        """Test that dummy users are listed on user page."""
        url = reverse('admin:core_user_changelist')
        resp = self.client.get(url)
        self.assertContains(resp, self.user.email)
        self.assertContains(resp, self.admin_user.email)


    def test_add_new_user_page(self):
        """Test that the add new user page works."""
        url = reverse('admin:core_user_add')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)