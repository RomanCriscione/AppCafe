
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from unittest.mock import patch

from .admin import UserRewardUnlockAdmin
from .models import UserRewardUnlock


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
class RewardReminderTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="usuario_recordatorio",
            email="recordatorio@example.com",
            password="TestPassword123!",
        )

        self.admin_user = User.objects.create_superuser(
            username="admin_recordatorio",
            email="admin_recordatorio@example.com",
            password="TestPassword123!",
        )

        self.unlock = UserRewardUnlock.objects.create(
            user=self.user,
            unlock_type=UserRewardUnlock.UnlockType.WELCOME,
            status=UserRewardUnlock.Status.PENDING,
        )

        self.model_admin = UserRewardUnlockAdmin(
            UserRewardUnlock,
            admin.site,
        )

        self.request = RequestFactory().post("/admin/")
        self.request.user = self.admin_user

        # Capturamos los mensajes del administrador sin
        # necesitar una sesión HTTP.
        self.messages = []
        self.model_admin.message_user = (
            lambda request, message, level=None:
            self.messages.append(message)
        )

        mail.outbox = []

    def send_reminders(self, queryset=None):
        if queryset is None:
            queryset = UserRewardUnlock.objects.all()

        self.model_admin.send_pending_reward_reminders(
            self.request,
            queryset,
        )

    def test_pending_unlock_sends_email(self):
        self.send_reminders()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn("beneficio", mail.outbox[0].subject.lower())
        self.assertIn("Mis Gotas", mail.outbox[0].body)

        self.unlock.refresh_from_db()
        self.assertIsNotNone(self.unlock.reminder_sent_at)

    def test_already_claimed_unlock_does_not_send(self):
        self.unlock.status = UserRewardUnlock.Status.CLAIMED
        self.unlock.save(update_fields=["status"])

        self.send_reminders()

        self.assertEqual(len(mail.outbox), 0)

        self.unlock.refresh_from_db()
        self.assertIsNone(self.unlock.reminder_sent_at)

    def test_multiple_unlocks_send_one_email(self):
        UserRewardUnlock.objects.create(
            user=self.user,
            unlock_type=UserRewardUnlock.UnlockType.MILESTONE,
            points_required=15,
            status=UserRewardUnlock.Status.PENDING,
        )

        self.send_reminders()

        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(
            UserRewardUnlock.objects.filter(
                user=self.user,
                reminder_sent_at__isnull=False,
            ).count(),
            2,
        )

    def test_reminder_is_not_sent_twice(self):
        self.send_reminders()
        self.send_reminders()

        self.assertEqual(len(mail.outbox), 1)

    def test_user_without_email_is_skipped(self):
        self.user.email = ""
        self.user.save(update_fields=["email"])

        self.send_reminders()

        self.assertEqual(len(mail.outbox), 0)

        self.unlock.refresh_from_db()
        self.assertIsNone(self.unlock.reminder_sent_at)

    @patch("reviews.admin.send_mail", side_effect=Exception("Error SMTP simulado"))
    def test_email_failure_does_not_mark_reminder_as_sent(self, mocked_send):
        self.send_reminders()

        self.unlock.refresh_from_db()

        self.assertIsNone(self.unlock.reminder_sent_at)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(mocked_send.call_count, 1)