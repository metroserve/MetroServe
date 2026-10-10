
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import UserProfile, EmailVerificationCode


CODE_LIFETIME_MINUTES = 10
MAX_CODE_ATTEMPTS = 5
RESEND_WAIT_SECONDS = 60


def _send_verification_code(user, purpose):
    """Invalidate old codes, create a new hashed code, and email it."""
    now = timezone.now()

    EmailVerificationCode.objects.filter(
        user=user,
        purpose=purpose,
        used_at__isnull=True,
    ).update(used_at=now)

    code = f'{secrets.randbelow(1_000_000):06d}'

    EmailVerificationCode.objects.create(
        user=user,
        purpose=purpose,
        code_hash=make_password(code),
        expires_at=now + timedelta(minutes=CODE_LIFETIME_MINUTES),
    )

    subject = (
        'Verify your MetroServe account'
        if purpose == 'registration'
        else 'Your MetroServe sign-in code'
    )

    message = (
        f'Hello {user.first_name or user.username},\n\n'
        f'Your MetroServe verification code is: {code}\n\n'
        f'This code expires in {CODE_LIFETIME_MINUTES} minutes '
        'and can only be used once.\n'
        'If you did not request this code, you can ignore this email.'
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def _start_verification(request, user, purpose):
    request.session['verification_user_id'] = user.pk
    request.session['verification_purpose'] = purpose

    _send_verification_code(user, purpose)


def register(request):
    if request.method == 'POST':
        data = request.POST
        errors = []

        username = data.get('username', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone_number', '').strip()
        password = data.get('password', '')
        confirm = data.get('password_confirm', '')

        if not all([
            username, first_name, last_name, email,
            phone, password, confirm
        ]):
            errors.append('All required fields must be completed.')

        if password != confirm:
            errors.append('Passwords do not match.')

        if User.objects.filter(username=username).exists():
            errors.append('That username is already in use.')

        if User.objects.filter(email__iexact=email).exists():
            errors.append('That email address is already registered.')

        if not errors:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=False,
                    )

                    profile, _ = UserProfile.objects.get_or_create(
                        user=user
                    )
                    profile.phone_number = phone
                    profile.role = 'citizen'
                    profile.save()

                    _start_verification(
                        request, user, 'registration'
                    )

            except Exception:
                # Avoid leaving an unusable account if email sending fails.
                if 'user' in locals():
                    user.delete()

                messages.error(
                    request,
                    'We could not send the verification email. '
                    'Please check the email address and try again.'
                )
                return render(
                    request,
                    'accounts/register.html',
                    {'errors': [], 'form_data': data},
                )

            messages.success(
                request,
                'A verification code has been sent. '
                'Check your email or the development terminal.'
            )
            return redirect('verify_email_code')

        return render(
            request,
            'accounts/register.html',
            {'errors': errors, 'form_data': data},
        )

    return render(
        request,
        'accounts/register.html',
        {'errors': [], 'form_data': {}},
    )


def citizen_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = User.objects.filter(email__iexact=email).first()

        if user and authenticate(
            request,
            username=user.username,
            password=password,
        ):
            if user.is_staff or user.is_superuser:
                messages.info(
                    request,
                    'Please use the appropriate staff or administrator portal.'
                )
                return redirect('staff_login')

            if not user.is_active:
                messages.error(
                    request,
                    'This account is not active yet. '
                    'Complete registration verification first.'
                )
                return redirect('login')

            try:
                _start_verification(request, user, 'login')
            except Exception:
                request.session.pop('verification_user_id', None)
                request.session.pop('verification_purpose', None)
                messages.error(
                    request,
                    'We could not send a verification code. '
                    'Please try again later.'
                )
                return redirect('login')

            messages.success(
                request,
                'A sign-in code has been sent to your email.'
            )
            return redirect('verify_email_code')

        messages.error(request, 'Invalid email or password.')

    return render(request, 'registration/login.html')


def verify_email_code(request):
    user_id = request.session.get('verification_user_id')
    purpose = request.session.get('verification_purpose')

    if purpose not in ('registration', 'login') or not user_id:
        messages.error(
            request,
            'Start registration or sign-in to request a verification code.'
        )
        return redirect('login')

    user = User.objects.filter(pk=user_id).first()

    if not user:
        request.session.pop('verification_user_id', None)
        request.session.pop('verification_purpose', None)
        messages.error(request, 'The account could not be found.')
        return redirect('login')

    if request.method == 'POST':
        # Allow a user to request a replacement code without
        # repeatedly sending email on every page refresh.
        if request.POST.get('action') == 'resend':
            recent_code = EmailVerificationCode.objects.filter(
                user=user,
                purpose=purpose,
                created_at__gte=timezone.now()
                - timedelta(seconds=RESEND_WAIT_SECONDS),
            ).exists()

            if recent_code:
                messages.error(
                    request,
                    'Please wait a minute before requesting another code.'
                )
            else:
                try:
                    _send_verification_code(user, purpose)
                    messages.success(
                        request,
                        'A new verification code has been sent.'
                    )
                except Exception:
                    messages.error(
                        request,
                        'We could not send a new code. Please try again later.'
                    )

            return redirect('verify_email_code')

        now = timezone.now()

        code_record = EmailVerificationCode.objects.filter(
            user=user,
            purpose=purpose,
            used_at__isnull=True,
            expires_at__gt=now,
        ).order_by('-created_at').first()

        if not code_record:
            messages.error(
                request,
                'Your code has expired or is no longer valid. '
                'Request a new code below.'
            )
            return render(
                request,
                'accounts/verify_email.html',
                {'email': user.email},
            )

        if code_record.attempts >= MAX_CODE_ATTEMPTS:
            code_record.used_at = now
            code_record.save(update_fields=['used_at'])
            messages.error(
                request,
                'Too many incorrect attempts. Request a new code.'
            )
            return render(
                request,
                'accounts/verify_email.html',
                {'email': user.email},
            )

        submitted_code = request.POST.get('code', '').strip()

        if not (
            len(submitted_code) == 6
            and submitted_code.isascii()
            and submitted_code.isdigit()
            and check_password(submitted_code, code_record.code_hash)
        ):
            code_record.attempts += 1

            if code_record.attempts >= MAX_CODE_ATTEMPTS:
                code_record.used_at = now

            code_record.save(update_fields=['attempts', 'used_at'])
            messages.error(
                request,
                'Incorrect verification code. Please try again.'
            )
            return render(
                request,
                'accounts/verify_email.html',
                {'email': user.email},
            )

        # Mark the code used before completing the verification.
        code_record.used_at = now
        code_record.save(update_fields=['used_at'])

        request.session.pop('verification_user_id', None)
        request.session.pop('verification_purpose', None)

        if purpose == 'registration':
            user.is_active = True
            user.save(update_fields=['is_active'])

            messages.success(
                request,
                'Email verified! You can now sign in with your email and password.'
            )
            return redirect('login')

        if not user.is_active or user.is_staff or user.is_superuser:
            messages.error(
                request,
                'This account cannot sign in through the resident portal.'
            )
            return redirect('login')

        login(request, user)

        return redirect('citizen_dashboard')

    return render(
        request,
        'accounts/verify_email.html',
        {'email': user.email},
    )


def staff_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user and user.is_staff and not user.is_superuser:
            login(request, user)
            return redirect('staff_dashboard')

        messages.error(
            request,
            'Invalid staff credentials or staff access is not authorised.'
        )

    return render(request, 'accounts/staff_login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        request.user.first_name = request.POST.get(
            'first_name', ''
        ).strip()
        request.user.last_name = request.POST.get(
            'last_name', ''
        ).strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save()

        profile_obj.phone_number = request.POST.get(
            'phone_number', ''
        ).strip()
        profile_obj.bio = request.POST.get('bio', '').strip()

        if request.FILES.get('profile_picture'):
            profile_obj.profile_picture = request.FILES[
                'profile_picture'
            ]

        profile_obj.save()
        messages.success(
            request,
            'Your MetroServe profile has been updated.'
        )
        return redirect('profile')

    return render(
        request,
        'accounts/profile.html',
        {'profile_obj': profile_obj},
    )
