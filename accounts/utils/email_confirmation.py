from accounts.models import EmailConfirmationToken


def create_email_confirmation_token(user):
    return EmailConfirmationToken.objects.create(user=user)
