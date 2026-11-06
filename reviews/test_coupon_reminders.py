from datetime import datetime, time, timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from .admin import UserCouponAdmin
from .models import Cafe, CafeReward, UserCoupon

from unittest.mock import patch


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
class CouponReminderTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="usuario_cupon",
            email="cupon@example.com",
            password="TestPassword123!",
        )

        self.admin_user = User.objects.create_superuser(
            username="admin_cupon",
            email="admin_cupon@example.com",
            password="TestPassword123!",
        )

        self.cafe = Cafe.objects.create(
            name="Café de prueba Gota",
            address="Calle de prueba 123",
            location="Quilmes",
        )

        self.reward = CafeReward.objects.create(
            cafe=self.cafe,
            name="Beneficio de prueba",
            reward_type=CafeReward.RewardType.TWO_FOR_ONE,
            user_text="2x1 en café",
        )

        self.coupon = UserCoupon.objects.create(
            user=self.user,
            cafe=self.cafe,
            reward=self.reward,
            reward_text_snapshot=self.reward.user_text,
            expires_at=timezone.now() + timedelta(days=7),
        )

        self.model_admin = UserCouponAdmin(
            UserCoupon,
            admin.site,
        )

        self.request = RequestFactory().post("/admin/")
        self.request.user = self.admin_user

        self.messages = []
        self.model_admin.message_user = (
            lambda request, message, level=None:
            self.messages.append(message)
        )

        mail.outbox = []

    def send_reminders(self, queryset=None):
        if queryset is None:
            queryset = UserCoupon.objects.all()

        self.model_admin.send_coupon_expiration_reminders(
            self.request,
            queryset,
        )

    def test_available_coupon_sends_email(self):
        self.send_reminders()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn(self.cafe.name, mail.outbox[0].body)
        self.assertIn(
            self.reward.user_text,
            mail.outbox[0].body,
        )

        self.coupon.refresh_from_db()
        self.assertIsNotNone(self.coupon.reminder_sent_at)


    def test_used_coupon_does_not_send(self):
        self.coupon.status = UserCoupon.Status.USED
        self.coupon.used_at = timezone.now()
        self.coupon.save(update_fields=["status", "used_at"])

        self.send_reminders()

        self.assertEqual(len(mail.outbox), 0)
        self.coupon.refresh_from_db()
        self.assertIsNone(self.coupon.reminder_sent_at)

    def test_expired_coupon_does_not_send(self):
        self.coupon.expires_at = timezone.now() - timedelta(days=1)
        self.coupon.save(update_fields=["expires_at"])

        self.send_reminders()

        self.assertEqual(len(mail.outbox), 0)
        self.coupon.refresh_from_db()
        self.assertIsNone(self.coupon.reminder_sent_at)

    def test_cancelled_coupon_does_not_send(self):
        self.coupon.status = UserCoupon.Status.CANCELLED
        self.coupon.save(update_fields=["status"])

        self.send_reminders()

        self.assertEqual(len(mail.outbox), 0)
        self.coupon.refresh_from_db()
        self.assertIsNone(self.coupon.reminder_sent_at)

    def test_user_without_email_does_not_send(self):
        self.user.email = ""
        self.user.save(update_fields=["email"])

        self.send_reminders()

        self.assertEqual(len(mail.outbox), 0)
        self.coupon.refresh_from_db()
        self.assertIsNone(self.coupon.reminder_sent_at)

    def test_reminder_is_not_sent_twice(self):
        self.send_reminders()
        self.send_reminders()

        self.assertEqual(len(mail.outbox), 1)

        self.coupon.refresh_from_db()
        self.assertIsNotNone(self.coupon.reminder_sent_at)

    def test_coupon_expires_in_two_days(self):
        now = timezone.now()
        expiration_date = timezone.localdate(now) + timedelta(days=2)

        self.coupon.expires_at = timezone.make_aware(
            datetime.combine(expiration_date, time(18, 0)),
            timezone.get_current_timezone(),
        )
        self.coupon.save(update_fields=["expires_at"])

        self.send_reminders()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            "Te quedan 2 días",
            mail.outbox[0].body,
        )

    def test_coupon_expires_today(self):
        today = timezone.localdate()
        self.coupon.expires_at = timezone.make_aware(
            datetime.combine(today, time(23, 59, 59)),
            timezone.get_current_timezone(),
        )
        self.coupon.save(update_fields=["expires_at"])

        self.send_reminders()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            "Tu cupón vence hoy",
            mail.outbox[0].body,
        )

    @patch("reviews.admin.send_mail")
    def test_smtp_error_does_not_mark_as_sent(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("Error SMTP simulado")

        self.send_reminders()

        self.coupon.refresh_from_db()

        self.assertIsNone(self.coupon.reminder_sent_at)
        self.assertEqual(mock_send_mail.call_count, 1)
        self.assertIsNone(self.coupon.reminder_claimed_at)

    def test_reserved_coupon_does_not_send(self):
        self.coupon.reminder_claimed_at = timezone.now()
        self.coupon.save(
            update_fields=["reminder_claimed_at"]
        )

        self.send_reminders()

        self.assertEqual(len(mail.outbox), 0)

        self.coupon.refresh_from_db()

        self.assertIsNone(self.coupon.reminder_sent_at)
        self.assertIsNotNone(self.coupon.reminder_claimed_at)

    def test_abandoned_reservation_can_be_released(self):
        old_claim = timezone.now() - timedelta(minutes=45)

        self.coupon.reminder_claimed_at = old_claim
        self.coupon.save(
            update_fields=["reminder_claimed_at"]
        )

        self.model_admin.release_abandoned_reminder_claims(
            self.request,
            UserCoupon.objects.filter(pk=self.coupon.pk),
        )

        self.coupon.refresh_from_db()

        self.assertIsNone(self.coupon.reminder_claimed_at)
        self.assertIsNone(self.coupon.reminder_sent_at)
        self.assertEqual(len(mail.outbox), 0)

    def test_recent_reservation_cannot_be_released(self):
        recent_claim = timezone.now() - timedelta(minutes=5)

        self.coupon.reminder_claimed_at = recent_claim
        self.coupon.save(
            update_fields=["reminder_claimed_at"]
        )

        self.model_admin.release_abandoned_reminder_claims(
            self.request,
            UserCoupon.objects.filter(pk=self.coupon.pk),
        )

        self.coupon.refresh_from_db()

        self.assertEqual(
            self.coupon.reminder_claimed_at,
            recent_claim,
        )
        self.assertIsNone(self.coupon.reminder_sent_at)
        self.assertEqual(len(mail.outbox), 0)

    def test_sent_reminder_reservation_cannot_be_released(self):
        old_claim = timezone.now() - timedelta(minutes=45)
        sent_at = timezone.now() - timedelta(minutes=40)

        self.coupon.reminder_claimed_at = old_claim
        self.coupon.reminder_sent_at = sent_at
        self.coupon.save(
            update_fields=[
                "reminder_claimed_at",
                "reminder_sent_at",
            ]
        )

        self.model_admin.release_abandoned_reminder_claims(
            self.request,
            UserCoupon.objects.filter(pk=self.coupon.pk),
        )

        self.coupon.refresh_from_db()

        self.assertEqual(
            self.coupon.reminder_claimed_at,
            old_claim,
        )
        self.assertEqual(
            self.coupon.reminder_sent_at,
            sent_at,
        )
        self.assertEqual(len(mail.outbox), 0)

    @patch("reviews.admin.send_mail")
    def test_smtp_failure_does_not_block_next_coupon(self, mock_send_mail):
        other_user = get_user_model().objects.create_user(
            username="otro_usuario_recordatorio",
            email="otro@example.com",
            password="TestPassword123!",
        )

        other_coupon = UserCoupon.objects.get(pk=self.coupon.pk)
        other_coupon.pk = None
        other_coupon.code = "GOTA-OTRO-TEST"
        other_coupon.qr_token = None
        other_coupon.user = other_user
        other_coupon.reminder_sent_at = None
        other_coupon.reminder_claimed_at = None
        other_coupon.save()

        mock_send_mail.side_effect = [
            Exception("Error SMTP simulado"),
            1,
        ]

        self.send_reminders()

        self.coupon.refresh_from_db()
        other_coupon.refresh_from_db()

        self.assertIsNone(self.coupon.reminder_sent_at)
        self.assertIsNone(self.coupon.reminder_claimed_at)
        self.assertIsNotNone(other_coupon.reminder_sent_at)
        self.assertIsNone(other_coupon.reminder_claimed_at)
        self.assertEqual(mock_send_mail.call_count, 2)

    @patch("reviews.admin.send_mail", return_value=0)
    def test_smtp_returns_zero_does_not_mark_as_sent(self, mock_send_mail):
        self.send_reminders()

        self.coupon.refresh_from_db()

        self.assertIsNone(self.coupon.reminder_sent_at)
        self.assertIsNone(self.coupon.reminder_claimed_at)
        self.assertEqual(mock_send_mail.call_count, 1)

    def test_coupon_cannot_be_reserved_twice(self):
        now = timezone.now()

        conditions = {
            "pk": self.coupon.pk,
            "status": UserCoupon.Status.AVAILABLE,
            "expires_at__gt": now,
            "used_at__isnull": True,
            "reminder_sent_at__isnull": True,
            "reminder_claimed_at__isnull": True,
        }

        first_reservation = UserCoupon.objects.filter(
            **conditions
        ).update(reminder_claimed_at=now)

        second_reservation = UserCoupon.objects.filter(
            **conditions
        ).update(reminder_claimed_at=timezone.now())

        self.assertEqual(first_reservation, 1)
        self.assertEqual(second_reservation, 0)