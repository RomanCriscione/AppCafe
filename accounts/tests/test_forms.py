from django.test import TestCase
from accounts.forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationFormTest(TestCase):

    def test_valid_form(self):
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')

    def test_passwords_must_match(self):
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'WrongPass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class CustomUserChangeFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_form_prefilled_with_instance(self):
        form = CustomUserChangeForm(instance=self.user)
        self.assertEqual(form.initial['username'], 'testuser')
        self.assertEqual(form.initial['email'], 'test@example.com')

    def test_form_updates_user(self):
        form_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
        }
        form = CustomUserChangeForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        updated_user = form.save()
        self.assertEqual(updated_user.username, 'updateduser')
        self.assertEqual(updated_user.email, 'updated@example.com')
