import tempfile
import shutil
import io
from PIL import Image
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp()

def generate_test_image():
    file = io.BytesIO()
    image = Image.new('RGB', (10, 10), 'red')
    image.save(file, 'JPEG')
    file.seek(0)
    return SimpleUploadedFile("test_avatar.jpg", file.read(), content_type="image/jpeg")

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class EditAvatarViewTests(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            age=30
        )
        self.client.login(username="testuser", password="password123")

    def test_avatar_upload(self):
        avatar_file = generate_test_image()

        response = self.client.post(
            reverse('edit_avatar'),
            {
                'username': self.user.username,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'avatar': avatar_file
            },
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
