
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.utils import timezone
from django.core import mail
from django.test import override_settings

from .models import (
    Cafe,
    Review,
    RewardActionRule,
    RewardClaim,
    RewardSettings,
    UserPointTransaction,
)
from .rewards import approve_reward_claim


class RewardClaimApprovalTests(TransactionTestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="usuario_prueba_gotas",
            email="usuario_gotas@example.com",
            password="TestPassword123!",
        )

        self.admin_user = User.objects.create_superuser(
            username="admin_prueba_gotas",
            email="admin_gotas@example.com",
            password="TestPassword123!",
        )

        self.cafe = Cafe.objects.create(
            name="Cafetería de prueba Gotas",
            address="Calle de prueba 123",
            location="Quilmes",
        )

        self.review = Review.objects.create(
            user=self.user,
            cafe=self.cafe,
            location="Quilmes",
            rating=5,
            comment="Reseña de prueba para reclamar Gotas.",
        )

        self.claim = RewardClaim.objects.create(
            user=self.user,
            cafe=self.cafe,
            review=self.review,
        )

        RewardSettings.objects.create(
            rewards_enabled=True,
            program_starts_at=timezone.now() - timedelta(days=1),
            welcome_reward_enabled=False,
        )

        RewardActionRule.objects.create(
            action=RewardActionRule.Action.REVIEW,
            points=5,
            is_active=True,
        )

        RewardActionRule.objects.create(
            action=RewardActionRule.Action.REVIEW_TAG_BONUS,
            points=2,
            is_active=True,
        )

    def test_approve_claim_awards_points(self):
        result = approve_reward_claim(
            claim=self.claim,
            resolved_by=self.admin_user,
            has_tag_bonus=False,
        )

        self.assertTrue(result["approved"])
        self.assertEqual(result["points"], 5)

        self.claim.refresh_from_db()

        self.assertEqual(
            self.claim.status,
            RewardClaim.Status.APPROVED,
        )

        self.assertIsNotNone(
            self.claim.review_transaction_id,
        )

        self.assertEqual(
            UserPointTransaction.objects.filter(
                user=self.user,
            ).count(),
            1,
        )

    def test_approve_claim_with_tag_bonus(self):
        result = approve_reward_claim(
            claim=self.claim,
            resolved_by=self.admin_user,
            has_tag_bonus=True,
        )

        self.assertTrue(result["approved"])
        self.assertEqual(result["points"], 7)

        self.claim.refresh_from_db()

        self.assertIsNotNone(
            self.claim.review_transaction_id,
        )
        self.assertIsNotNone(
            self.claim.tag_bonus_transaction_id,
        )

        self.assertEqual(
            UserPointTransaction.objects.filter(
                user=self.user,
            ).count(),
            2,
        )

    def test_approving_twice_does_not_duplicate_points(self):
        first_result = approve_reward_claim(
            claim=self.claim,
            resolved_by=self.admin_user,
            has_tag_bonus=False,
        )

        second_result = approve_reward_claim(
            claim=self.claim,
            resolved_by=self.admin_user,
            has_tag_bonus=False,
        )

        self.assertTrue(first_result["approved"])
        self.assertFalse(second_result["approved"])

        self.assertEqual(
            second_result["reason"],
            "claim_already_resolved",
        )

        self.assertEqual(
            UserPointTransaction.objects.filter(
                user=self.user,
            ).count(),
            1,
        )

    def test_claim_without_review_cannot_be_approved(self):
        self.claim.review = None
        self.claim.save(update_fields=["review"])

        result = approve_reward_claim(
            claim=self.claim,
            resolved_by=self.admin_user,
        )

        self.assertFalse(result["approved"])
        self.assertEqual(
            result["reason"],
            "review_required",
        )

        self.assertFalse(
            UserPointTransaction.objects.filter(
                user=self.user,
            ).exists()
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
    )
    def test_approval_email_is_sent_only_once(self):
        mail.outbox = []

        first_result = approve_reward_claim(
            claim=self.claim,
            resolved_by=self.admin_user,
            has_tag_bonus=False,
        )

        self.assertTrue(first_result["approved"])
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.to, [self.user.email])
        self.assertIn("aprobado", email.subject.lower())
        self.assertIn(self.cafe.name, email.body)
        self.assertIn("5 Gotas", email.body)

        second_result = approve_reward_claim(
            claim=self.claim,
            resolved_by=self.admin_user,
            has_tag_bonus=False,
        )

        self.assertFalse(second_result["approved"])
        self.assertEqual(len(mail.outbox), 1)