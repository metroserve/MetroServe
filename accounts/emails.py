from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse


def send_verification_email(request, user):
    """
    Sends the email-verification message to `user`.
    The link points to verify_email with the user's current token.
    """
    profile = user.profile
    verify_url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'token': str(profile.verification_token)})
    )

    context = {'user': user, 'verify_url': verify_url}

    subject = 'Verify your MetroServe account'
    text_message = render_to_string('accounts/emails/verify_email.txt', context)
    html_message = render_to_string('accounts/emails/verify_email.html', context)

    send_mail(
        subject=subject,
        message=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )