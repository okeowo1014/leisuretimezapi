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

from index.models import CustomUser, Notification, BlogPost

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
        # Always return the same response to prevent account enumeration
        try:
            user = CustomUser.objects.get(email=email)
            if not user.is_active:
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
                try:
                    email_msg.send()
                except Exception:
                    logger.exception("Failed to send activation email to %s", email)

                user.activation_sent_at = timezone.now()
                user.save()
        except CustomUser.DoesNotExist:
            pass  # Silently ignore — same response returned either way

        return Response(
            {'message': 'If the account exists and is not yet active, an activation email has been sent.'}
        )

    return Response({'error': 'POST method required.'}, status=405)


def forgot_password(request):
    """Handle the forgot password form submission."""
    if request.method == 'POST':
        email = request.POST.get('email')
        # Always return the same response to prevent account enumeration
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
            try:
                email_msg.send()
            except Exception:
                logger.exception("Failed to send password reset email to %s", email)
        except CustomUser.DoesNotExist:
            pass  # Silently ignore — same response returned either way

        return Response(
            {'message': 'If an account with that email exists, a password reset link has been sent.'}
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


def create_notification(user, notification_type, title, message, booking=None):
    """Create an in-app notification and return it."""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        booking=booking,
    )


def notify_booking_confirmed(booking):
    """Send booking confirmation notification + email."""
    user = booking.customer.user
    create_notification(
        user=user,
        notification_type='booking_confirmed',
        title='Booking Confirmed',
        message=(
            f'Your booking {booking.booking_id} for {booking.package} '
            f'has been confirmed. Travel dates: {booking.datefrom} to {booking.dateto}.'
        ),
        booking=booking,
    )
    try:
        send_mail(
            subject=f'Booking Confirmed — {booking.booking_id}',
            message=(
                f'Dear {booking.firstname},\n\n'
                f'Your booking {booking.booking_id} has been confirmed!\n\n'
                f'Package: {booking.package}\n'
                f'Travel dates: {booking.datefrom} to {booking.dateto}\n'
                f'Guests: {booking.adult} adults, {booking.children} children\n'
                f'Amount paid: {booking.price}\n\n'
                f'Thank you for choosing Leisuretimez!\n\n'
                f'Best regards,\nLeisuretimez Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.email],
            fail_silently=True,
        )
    except Exception:
        logger.exception("Failed to send booking confirmation email for %s", booking.booking_id)


def notify_payment_received(booking, amount, method):
    """Send payment received notification + email."""
    user = booking.customer.user
    create_notification(
        user=user,
        notification_type='payment_received',
        title='Payment Received',
        message=(
            f'Payment of {amount} received for booking {booking.booking_id} '
            f'via {method}.'
        ),
        booking=booking,
    )
    try:
        send_mail(
            subject=f'Payment Received — {booking.booking_id}',
            message=(
                f'Dear {booking.firstname},\n\n'
                f'We have received your payment of {amount} for booking '
                f'{booking.booking_id} via {method}.\n\n'
                f'Your booking is now being processed.\n\n'
                f'Best regards,\nLeisuretimez Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.email],
            fail_silently=True,
        )
    except Exception:
        logger.exception("Failed to send payment received email for %s", booking.booking_id)


def notify_booking_cancelled(booking, refund_amount):
    """Send booking cancellation notification + email."""
    user = booking.customer.user
    refund_msg = (
        f' A refund of {refund_amount} will be credited to your wallet.'
        if refund_amount > 0
        else ' No refund is applicable per our cancellation policy.'
    )
    create_notification(
        user=user,
        notification_type='booking_cancelled',
        title='Booking Cancelled',
        message=f'Your booking {booking.booking_id} has been cancelled.{refund_msg}',
        booking=booking,
    )
    try:
        send_mail(
            subject=f'Booking Cancelled — {booking.booking_id}',
            message=(
                f'Dear {booking.firstname},\n\n'
                f'Your booking {booking.booking_id} has been cancelled.\n'
                f'{refund_msg.strip()}\n\n'
                f'If you have any questions, please contact our support team.\n\n'
                f'Best regards,\nLeisuretimez Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.email],
            fail_silently=True,
        )
    except Exception:
        logger.exception("Failed to send cancellation email for %s", booking.booking_id)


def notify_refund_processed(booking, refund_amount):
    """Send refund processed notification."""
    user = booking.customer.user
    create_notification(
        user=user,
        notification_type='refund_processed',
        title='Refund Processed',
        message=(
            f'A refund of {refund_amount} for booking {booking.booking_id} '
            f'has been credited to your wallet.'
        ),
        booking=booking,
    )


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


# ---------------------------------------------------------------------------
# Push Notification Utilities
# ---------------------------------------------------------------------------

def notify_new_blog_post_email(post):
    """Send email to all active users about a new blog post.

    This is an optional heavy operation — should be called asynchronously
    in production. For now it sends synchronously with fail_silently=True.
    """
    from index.models import CustomUser
    users = CustomUser.objects.filter(is_active=True).exclude(pk=post.author.pk)
    for user in users.iterator():
        try:
            send_mail(
                subject=f'New on the Leisuretimez Blog: {post.title}',
                message=(
                    f'Hi {user.firstname},\n\n'
                    f'We just published a new blog post:\n\n'
                    f'"{post.title}"\n'
                    f'{post.excerpt or post.content[:200]}...\n\n'
                    f'Read it here: {settings.FRONTEND_URL}/blog/{post.slug}\n\n'
                    f'Best regards,\nLeisuretimez Team'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            logger.exception("Failed to send blog notification email to %s", user.email)


def notify_welcome(user):
    """Send a welcome notification after registration."""
    create_notification(
        user=user,
        notification_type='system',
        title='Welcome to Leisuretimez!',
        message=(
            'Welcome aboard! Explore our travel packages, read our blog, '
            'and start planning your next adventure.'
        ),
    )


def notify_promo_broadcast(promo_code, message_text=None):
    """Broadcast a promo notification to all active users."""
    from index.models import CustomUser
    users = CustomUser.objects.filter(is_active=True)
    msg = message_text or (
        f'Use code "{promo_code.code}" to get '
        f'{"{}% off".format(promo_code.discount_value) if promo_code.discount_type == "percentage" else "${} off".format(promo_code.discount_value)}'
        f' your next booking! Valid until {promo_code.valid_to.strftime("%b %d, %Y")}.'
    )
    count = 0
    for user in users.iterator():
        create_notification(
            user=user,
            notification_type='promo',
            title='Special Offer!',
            message=msg,
        )
        count += 1
    logger.info("Sent promo notification to %d users for code %s", count, promo_code.code)
    return count
