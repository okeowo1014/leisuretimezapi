# views.py

from datetime import datetime, timedelta
from django.utils import timezone
# views.py
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from index.models import CustomUser
import os
from django.conf import settings
import base64
from django.core.mail import send_mail
from django.core.mail import EmailMessage

def encode_user_pk(user_pk):
    # Encode the user PK as a string, then convert it to bytes and base64 encode
    encoded = base64.urlsafe_b64encode(str(user_pk).encode('utf-8')).decode('utf-8')
    return encoded

def decode_user_pk(encoded_pk):
    # Decode the Base64 encoded string, then convert it back to an integer
    decoded = base64.urlsafe_b64decode(encoded_pk.encode('utf-8')).decode('utf-8')
    return int(decoded)


def resend_activation_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            # Check if the user is already active
            if user.is_active:
                messages.info(request, 'Your account is already active. Please log in.')
                return redirect('index:customer-login')  # Replace 'login' with your actual login URL name

            # Check if the activation link was recently sent (e.g., limit to 1 email per hour)
            # if user.activation_sent_at and \
            #   user.activation_sent_at > timezone.now() - timedelta(hours=1):
            #     messages.error(request, 'Activation email recently sent. Please check your inbox.')
            #     return redirect('index:customer-login')  # Replace with appropriate redirect

            # Generate new activation token and send email
            # Send email verification
            current_site = get_current_site(request)
            mail_subject = 'Activate your account'
            message = render_to_string('myadmin/verifymail.html', {
                'user': user,
                'domain': current_site.domain,
                'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            email = EmailMessage(
                mail_subject, message, to=[email]
            )
            email.content_subtype = "html"  # Set the content type to HTML
            email.send()

            # Update activation sent timestamp
            user.activation_sent_at = timezone.now()
            user.save()
            messages.success(request, 'Activation email sent. Please check your inbox.')
            return redirect('index:customer-login')  # Replace 'login' with your actual login URL name

        except CustomUser.DoesNotExist:
            messages.error(request, 'User with this email address does not exist.')
            return redirect('index:customer-login')  # Replace with appropriate redirect

    return render(request, 'index/resend-activation-page.html')


def activate_account(request, utoken, token):
    uid = urlsafe_base64_decode(utoken).decode()
    user = CustomUser.objects.get(pk=uid)
    try:
        uid = urlsafe_base64_decode(utoken).decode()
        user = CustomUser.objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            # Check if the activation link has expired (e.g., expires in 24 hours)
            expiry_time = user.activation_sent_at + timedelta(hours=24)  # Adjust as needed
            if timezone.now() > expiry_time:
                messages.error(request, 'Activation link has expired. Please request a new one.')
                return redirect('index:resend-activation-page')

            # Activate user account
            user.is_active = True
            user.save()
            messages.success(request, 'Your account has been activated. You can now log in')
            return redirect('index:customer-login')

              # Replace 'login' with your actual login URL name
        else:
            messages.error(request, 'Activation link is invalid.')
            return redirect('index:resend-activation-page')
    
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Activation link is invalid.')
        return redirect('index:resend-activation-page')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        user = CustomUser.objects.get(email=email)
        print(user)
        try:
            user = CustomUser.objects.get(email=email)
            print(user)
            # Generate a password reset token
            current_site = get_current_site(request)
            email_subject = 'Reset Your Password'
            email_body = render_to_string('myadmin/password_reset_email.html', {
                 'user': user,
                'domain': current_site.domain,
                'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })

            # Send the email
            email = EmailMessage(
                email_subject,
                email_body,
                to=[email],
            )
            email.content_subtype = "html"  # Set the content type to HTML
            email.send()
            messages.success(request, 'An email has been sent with instructions to reset your password.')
            return redirect('index:customer-login')  # Replace with your own URL for login
        except:
            messages.error(request, 'No user found with that email address.')
            return redirect('index:index')
    
    return render(request, 'index/forgot-password-page.html')

def reset_password_confirm(request, utoken, token):
    try:
        uid = urlsafe_base64_decode(utoken).decode()
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST['password']
            user.set_password(password)
            user.save()
            messages.success(request, 'Your password has been reset successfully.')
            return redirect('index:customer-login')  # Replace with your own URL for login
        
        return render(request, 'index/reset_password_confirm.html',context={'utoken':utoken,'token':token})
    else:
        messages.error(request, 'The reset password link is invalid. Please request a new one.')
        return redirect('index:reset-password-page')  # Replace with your own URL for reset_password_request
  
        
# from_email=settings.DEFAULT_FROM_EMAIL,


# def send_invoice_email(customer_email, invoice_id, pdf_path):
#     # Create the email
#     subject = f"Invoice #{invoice_id}"
#     message = "Please find your invoice attached."
#     email = EmailMessage(
#         subject=subject,
#         body=message,
#         to=[customer_email],
#     )

#     # Attach the PDF file from memory location
#     if os.path.exists(pdf_path):
#         with open(pdf_path, 'rb') as pdf_file:
#             email.attach(f"invoice_{invoice_id}.pdf", pdf_file.read(), 'application/pdf')

#     # Send the email
#     email.send()

# This function should be called after successful



def send_invoice_email(customer_email, customer_name, invoice_id, pdf_path):
    # Email subject and message
    subject = f"Thank You for Your Purchase! Invoice #{invoice_id}"
    message = f"""
Dear {customer_name},

Thank you for your recent purchase! We truly appreciate your trust in us, and we're delighted to have you as our valued customer.

Attached is the invoice for your order #{invoice_id}. Please keep it for your records. If you have any questions or need further assistance, feel free to reach out to us at any time.

We strive to provide the best service and products for you, and we hope that you are completely satisfied with your purchase. Your support means the world to us, and we look forward to serving you again in the future.

Thank you once again for choosing us!

Best regards,
Leisuretimez
Customer Support Team
{settings.DEFAULT_FROM_EMAIL}
    """

    # Create the email
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[customer_email],
    )

    # Attach the PDF file from memory location
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as pdf_file:
            email.attach(f"invoice_{invoice_id}.pdf", pdf_file.read(), 'application/pdf')

    # Send the email
    email.send()


def send_contact_email(contact_data):
    """
    Send email notification for contact form submission
    """
    # Email to admin
    admin_subject = f'New Contact Form Submission: {contact_data["subject"]}'
    admin_message = f"""
    New contact form submission received:
    
    Name: {contact_data['fullname']}
    Email: {contact_data['email']}
    Subject: {contact_data['subject']}
    
    Message:
    {contact_data['message']}
    """
    
    # Send to admin
    send_mail(
        subject=admin_subject,
        message=admin_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=False,
    )
    
    # Auto-reply to user
    user_subject = f'We received your message: {contact_data["subject"]}'
    user_message = f"""
    Dear {contact_data['fullname']},
    
    Thank you for contacting us. We have received your message and will get back to you shortly.
    
    Your message details:
    Subject: {contact_data['subject']}
    Message:
    {contact_data['message']}
    
    Best regards,
    Your Company Name
    """
    
    # Send to user
    send_mail(
        subject=user_subject,
        message=user_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[contact_data['email']],
        fail_silently=False,
    )