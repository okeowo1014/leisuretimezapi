# serializers.py
from rest_framework import serializers
from .models import Event, EventImage, Booking, Package, Invoice, Payment, CustomerProfile

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ['id', 'image']

class EventSerializer(serializers.ModelSerializer):
    event_images = EventImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Event
        fields = ['id', 'name', 'country', 'continent', 'description', 
                 'main_image', 'services', 'status', 'event_images']

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ['id', 'address', 'city', 'state', 'country', 'phone', 
                 'profession', 'date_of_birth', 'marital_status']

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['booking_id', 'invoice_id', 'checkout_session_id', 
                           'payment_status', 'status', 'created_at', 'updated_at']

    def create(self, validated_data):
        from .utils import generate_booking_id  # Assuming this utility function exists
        validated_data['booking_id'] = generate_booking_id()
        return super().create(validated_data)

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['invoice_id', 'status', 'created_at', 'updated_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['payment_id', 'status', 'created_at', 'updated_at']

# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import stripe
import requests
from django.shortcuts import get_object_or_404

stripe.api_key = settings.STRIPE_SECRET_KEY

class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.filter(status='active').order_by('-id')
    serializer_class = EventSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country=country)
        return queryset

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(customer__user=self.request.user)

    def perform_create(self, serializer):
        customer = CustomerProfile.objects.get(user=self.request.user)
        serializer.save(customer=customer)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    try:
        data = request.data
        booking = get_object_or_404(Booking, booking_id=data.get('booking_id'))
        
        intent = stripe.PaymentIntent.create(
            amount=int(booking.price * 100),  # Convert to cents
            currency='usd',
            automatic_payment_methods={'enabled': True},
            metadata={'booking_id': booking.booking_id},
            receipt_email=booking.email
        )
        
        return Response({
            'clientSecret': intent.client_secret
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    try:
        booking = get_object_or_404(Booking, booking_id=request.data.get('booking_id'))
        
        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Booking: {booking.booking_id}',
                    },
                    'unit_amount': int(booking.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(f'/api/bookings/complete/{booking.booking_id}/'),
            cancel_url=request.build_absolute_uri('/api/bookings/canceled/'),
            metadata={'booking_id': booking.booking_id}
        )
        
        booking.checkout_session_id = session.id
        booking.save()
        
        return Response({'checkout_url': session.url})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_complete(request, booking_id):
    try:
        booking = get_object_or_404(Booking, booking_id=booking_id)
        if not booking.checkout_session_id:
            return Response({'error': 'No checkout session found'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        session = stripe.checkout.Session.retrieve(booking.checkout_session_id)
        if session.payment_status == "paid":
            booking.payment_status = "paid"
            booking.status = "confirmed"
            booking.save()
            
            # Create and process invoice
            package = Package.objects.get(package_id=booking.package)
            invoice = create_package_invoice(booking, package)
            if invoice:
                # Update package statistics
                package.submissions += 1
                package.bookings.add(booking)
                package.save()
                
                # Generate PDF invoice
                invoice_url = request.build_absolute_uri(f'/print-invoice/{invoice.invoice_id}/')
                pdf_path = publish_invoice(invoice_url, booking.booking_id)
                
                # Send email
                customer_name = f'{booking.firstname} {booking.lastname}'
                send_invoice_email(booking.email, customer_name, invoice.invoice_id, pdf_path)
                
                return Response({'status': 'success', 'message': 'Payment processed successfully'})
            
            return Response({'error': 'Failed to create invoice'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'Payment not completed'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def publish_invoice(request, invoice_id):
    try:
        invoice = get_object_or_404(Invoice, invoice_id=invoice_id)
        response = requests.post(
            'https://api.pdfshift.io/v3/convert/pdf',
            auth=('api', settings.PDFSHIFT_API_KEY),
            json={
                "source": request.build_absolute_uri(f'/print-invoice/{invoice_id}/'),
                "landscape": False,
                "use_print": False
            }
        )
        response.raise_for_status()
        
        return Response({'pdf_url': response.url})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'events', views.EventViewSet)
router.register(r'bookings', views.BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
    path('payments/create-intent/', views.create_payment_intent),
    path('payments/create-checkout-session/', views.create_checkout_session),
    path('bookings/complete/<str:booking_id>/', views.booking_complete),
    path('invoices/<str:invoice_id>/publish/', views.publish_invoice),
]


# serializers.py
from rest_framework import serializers
from .models import Contact

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['fullname', 'email', 'subject', 'message']
        
# utils.py
from django.core.mail import send_mail
from django.conf import settings

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

# views.py
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ContactSerializer
from .utils import send_contact_email

@api_view(['POST'])
def contact_submit(request):
    """
    API endpoint for submitting contact form messages
    """
    serializer = ContactSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Save the contact message
            contact = serializer.save()
            
            # Send email notifications
            send_contact_email(serializer.validated_data)
            
            return Response({
                'status': 'success',
                'message': 'Your message has been sent successfully. We will contact you soon.'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'status': 'error',
        'message': 'Invalid data provided',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('contact/', views.contact_submit, name='api-contact-submit'),
]

# settings.py additions (add to your existing settings)
"""
# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-host'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-email-password'
DEFAULT_FROM_EMAIL = 'Your Company <noreply@yourcompany.com>'
ADMIN_EMAIL = 'admin@yourcompany.com'
"""