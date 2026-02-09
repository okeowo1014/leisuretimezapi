"""
Utility functions for account activation, password reset, and email sending.
"""

import logging
import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.decorators import api_view
from rest_framework.response import Response

from index.models import CustomUser

logger = logging.getLogger(__name__)


def encode_user_pk(user_pk):
    """Encode a user PK as a URL-safe base64 string."""
    import base64
    return base64.urlsafe_b64encode(str(user_pk).encode('utf-8')).decode('utf-8')


def decode_user_pk(encoded_pk):
    """Decode a URL-safe base64 string back to a user PK integer."""
    import base64
    return int(
        base64.urlsafe_b64decode(encoded_pk.encode('utf-8')).decode('utf-8')
    )


def activate_account(request, utoken, token):
    """Activate a user account via the emailed verification link."""
    try:
        uid = urlsafe_base64_decode(utoken).decode()
        user = CustomUser.objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            expiry_time = user.activation_sent_at + timedelta(hours=24)
            if timezone.now() > expiry_time:
                return Response(
                    {'error': 'Activation link has expired. Please request a new one.'},
                    status=400,
                )

            user.is_active = True
            user.save()
            return redirect(f'{settings.FRONTEND_URL}/login?activated=true')
        else:
            return Response(
                {'error': 'Activation link is invalid.'}, status=400
            )

    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        logger.exception("Invalid activation link")
        return Response(
            {'error': 'Activation link is invalid.'}, status=400
        )


def resend_activation_email(request):
    """Resend the account activation email (web form handler)."""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            if user.is_active:
                return Response(
                    {'message': 'Your account is already active. Please log in.'}
                )

            current_site = get_current_site(request)
            message = render_to_string('myadmin/verifymail.html', {
                'user': user,
                'domain': current_site.domain,
                'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            email_msg = EmailMessage(
                'Activate your account', message, to=[email]
            )
            email_msg.content_subtype = 'html'
            email_msg.send()

            user.activation_sent_at = timezone.now()
            user.save()
            return Response({'message': 'Activation email sent.'})

        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User with this email does not exist.'}, status=404
            )

    return Response({'error': 'POST method required.'}, status=405)


def forgot_password(request):
    """Handle the forgot password form submission."""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            current_site = get_current_site(request)
            email_body = render_to_string('myadmin/password_reset_email.html', {
                'user': user,
                'domain': current_site.domain,
                'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            email_msg = EmailMessage(
                'Reset Your Password', email_body, to=[email]
            )
            email_msg.content_subtype = 'html'
            email_msg.send()
            return Response({'message': 'Password reset email sent.'})
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'No user found with that email address.'}, status=404
            )

    return Response({'error': 'POST method required.'}, status=405)


def reset_password_confirm(request, utoken, token):
    """Confirm a password reset using the token from the email."""
    try:
        uid = urlsafe_base64_decode(utoken).decode()
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            if password:
                user.set_password(password)
                user.save()
                return Response({'message': 'Password reset successfully.'})
            return Response(
                {'error': 'Password is required.'}, status=400
            )
        return Response({'message': 'Token is valid. Submit new password via POST.'})

    return Response(
        {'error': 'The reset password link is invalid or expired.'}, status=400
    )


def send_invoice_email(customer_email, customer_name, invoice_id, pdf_path):
    """Send an invoice email with the PDF attached."""
    subject = f"Thank You for Your Purchase! Invoice #{invoice_id}"
    message = (
        f"Dear {customer_name},\n\n"
        f"Thank you for your recent purchase! We truly appreciate your trust "
        f"in us, and we're delighted to have you as our valued customer.\n\n"
        f"Attached is the invoice for your order #{invoice_id}. Please keep it "
        f"for your records. If you have any questions or need further assistance, "
        f"feel free to reach out to us at any time.\n\n"
        f"We strive to provide the best service and products for you, and we "
        f"hope that you are completely satisfied with your purchase. Your support "
        f"means the world to us, and we look forward to serving you again in the "
        f"future.\n\n"
        f"Thank you once again for choosing us!\n\n"
        f"Best regards,\n"
        f"Leisuretimez\n"
        f"Customer Support Team\n"
        f"{settings.DEFAULT_FROM_EMAIL}"
    )

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[customer_email],
    )

    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as pdf_file:
            email.attach(
                f"invoice_{invoice_id}.pdf", pdf_file.read(), 'application/pdf'
            )

    email.send()


def send_contact_email(contact_data):
    """Send email notifications for a contact form submission."""
    admin_subject = f'New Contact Form Submission: {contact_data["subject"]}'
    admin_message = (
        f'New contact form submission received:\n\n'
        f'Name: {contact_data["fullname"]}\n'
        f'Email: {contact_data["email"]}\n'
        f'Subject: {contact_data["subject"]}\n\n'
        f'Message:\n{contact_data["message"]}'
    )

    send_mail(
        subject=admin_subject,
        message=admin_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=False,
    )

    user_subject = f'We received your message: {contact_data["subject"]}'
    user_message = (
        f'Dear {contact_data["fullname"]},\n\n'
        f'Thank you for contacting us. We have received your message and '
        f'will get back to you shortly.\n\n'
        f'Your message details:\n'
        f'Subject: {contact_data["subject"]}\n'
        f'Message:\n{contact_data["message"]}\n\n'
        f'Best regards,\n'
        f'Leisuretimez Support Team'
    )

    send_mail(
        subject=user_subject,
        message=user_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[contact_data['email']],
        fail_silently=False,
    )
