"""
API views for the Leisuretimez travel booking platform.

Handles packages, bookings, invoices, payments, profiles, contacts, and search.
"""

import json
import logging
import os
import uuid
from decimal import Decimal

import requests
import stripe
from django.conf import settings
from django.db import IntegrityError, models, transaction as db_transaction
from django.db.models import BooleanField, Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Avg, Count
from django.utils import timezone

from index.countrylist import get_country_info
from index.utils import (
    create_notification, notify_booking_cancelled, notify_booking_confirmed,
    notify_payment_received, notify_refund_processed,
    send_contact_email, send_invoice_email,
)

from .models import (
    Booking, Carousel, CustomerProfile, Destination, Event, GuestImage,
    Invoice, Locations, Notification, Package, PackageImage, Payment,
    PersonalisedBooking, PromoCode, Review, SupportMessage, SupportTicket,
    Transaction, Wallet,
)
from .serializers import (
    BookingSerializer, CancelBookingSerializer, CarouselSerializer,
    ContactSerializer, CustomerProfileSerializer,
    CustomerProfileUpdateSerializer, DestinationSerializer,
    EventSerializer, GuestImageSerializer, InvoiceSerializer,
    LocationsSerializer, ModifyBookingSerializer, NotificationSerializer,
    PackageSerializer, PackageImageSerializer,
    PersonalisedBookingCreateSerializer, PersonalisedBookingSerializer,
    PromoCodeApplySerializer, ReviewCreateSerializer, ReviewSerializer,
    SupportReplySerializer, SupportTicketCreateSerializer,
    SupportTicketSerializer,
)

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


# ---------------------------------------------------------------------------
# ID Generators
# ---------------------------------------------------------------------------

def generate_booking_id():
    """Generate a unique booking ID with BKN prefix."""
    return 'BKN' + uuid.uuid4().hex[:6].upper()


def generate_payment_id():
    """Generate a unique payment ID with PMT prefix."""
    return 'PMT' + uuid.uuid4().hex[:6].upper()


def generate_transaction_id():
    """Generate a unique transaction ID with TXN prefix."""
    return 'TXN' + uuid.uuid4().hex[:16].upper()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_packages_queryset(user):
    """Return packages annotated with is_saved for the given user."""
    qs = Package.objects.filter(status='active').order_by('-id', 'category')
    if user.is_authenticated:
        return qs.annotate(
            is_saved=Exists(user.saved_packages.filter(pk=OuterRef('pk')))
        )
    return qs.annotate(
        is_saved=models.Value(False, output_field=BooleanField())
    )


def get_price(pid, adult=0, children=0):
    """Calculate the price for a package based on guest counts."""
    package = Package.objects.get(package_id=pid)
    if package.price_option == 'fixed':
        return package.fixed_price

    if not package.discount_price:
        return Decimal('0.00')

    offers = package.discount_price.split('-')
    offers = [offer.split(',') for offer in offers if len(offer.split(',')) >= 3]
    offers = [
        {
            'adult': int(offer[0]),
            'children': int(offer[1]),
            'price': Decimal(offer[2]),
        }
        for offer in offers
    ]
    matching_offer = next(
        (
            offer for offer in offers
            if offer['adult'] >= adult and offer['children'] >= children
        ),
        None,
    )
    return matching_offer['price'] if matching_offer else Decimal('0.00')


def _next_invoice_number():
    """Generate the next sequential invoice number based on the latest invoice by ID."""
    last_invoice = Invoice.objects.order_by('-id').first()
    if not last_invoice:
        return 'INV-000001'
    current_num = int(last_invoice.invoice_id.split('-')[1])
    return f'INV-{str(current_num + 1).zfill(6)}'


# ---------------------------------------------------------------------------
# Homepage & Package Views
# ---------------------------------------------------------------------------

@api_view(['GET'])
def index(request):
    """Return homepage data: active packages, destinations, events, and carousel."""
    packages = _get_packages_queryset(request.user)
    destinations = Destination.objects.filter(status='active')
    events = Event.objects.filter(status='active')
    carousel = Carousel.objects.filter(is_active=True)
    return Response({
        'packages': PackageSerializer(packages, many=True).data,
        'destinations': DestinationSerializer(destinations, many=True).data,
        'events': EventSerializer(events, many=True).data,
        'carousel': CarouselSerializer(carousel, many=True).data,
    })


@api_view(['GET'])
def package_list(request):
    """Return all active packages with saved status.

    Query params:
        search: keyword search on name/description
        continent: filter by continent
        country: filter by country
        category: filter by category
        min_price: minimum fixed_price
        max_price: maximum fixed_price
        min_duration: minimum duration (days)
        max_duration: maximum duration (days)
        sort_by: 'price', '-price', 'duration', '-duration', 'name', '-name', 'newest'
    """
    packages = _get_packages_queryset(request.user)

    search = request.GET.get('search')
    if search:
        packages = packages.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    continent = request.GET.get('continent')
    if continent:
        packages = packages.filter(continent__iexact=continent)

    country = request.GET.get('country')
    if country:
        packages = packages.filter(country__iexact=country)

    category = request.GET.get('category')
    if category:
        packages = packages.filter(category__iexact=category)

    min_price = request.GET.get('min_price')
    if min_price:
        try:
            packages = packages.filter(fixed_price__gte=Decimal(min_price))
        except Exception:
            pass

    max_price = request.GET.get('max_price')
    if max_price:
        try:
            packages = packages.filter(fixed_price__lte=Decimal(max_price))
        except Exception:
            pass

    min_duration = request.GET.get('min_duration')
    if min_duration:
        try:
            packages = packages.filter(duration__gte=int(min_duration))
        except (ValueError, TypeError):
            pass

    max_duration = request.GET.get('max_duration')
    if max_duration:
        try:
            packages = packages.filter(duration__lte=int(max_duration))
        except (ValueError, TypeError):
            pass

    sort_by = request.GET.get('sort_by', '')
    sort_map = {
        'price': 'fixed_price',
        '-price': '-fixed_price',
        'duration': 'duration',
        '-duration': '-duration',
        'name': 'name',
        '-name': '-name',
        'newest': '-created_at',
    }
    if sort_by in sort_map:
        packages = packages.order_by(sort_map[sort_by])

    return Response(PackageSerializer(packages, many=True).data)


@api_view(['GET'])
def package_details(request, pid):
    """Return details for a specific package including images."""
    package = get_object_or_404(Package, package_id=pid)
    package_images = PackageImage.objects.filter(package=package)
    guest_images = GuestImage.objects.filter(package=package)
    return Response({
        'package': PackageSerializer(package).data,
        'package_images': PackageImageSerializer(package_images, many=True).data,
        'guest_images': GuestImageSerializer(guest_images, many=True).data,
    })


# ---------------------------------------------------------------------------
# Profile & Account Views
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def personal_booking(request):
    """Return the authenticated user's customer profile."""
    profile = get_object_or_404(CustomerProfile, user=request.user)
    return Response(CustomerProfileSerializer(profile).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_history(request):
    """Return the authenticated user's booking history."""
    history = Booking.objects.filter(customer__user=request.user)
    return Response(BookingSerializer(history, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_settings(request):
    """Return profile and booking history for account settings page."""
    profile = get_object_or_404(CustomerProfile, user=request.user)
    history = Booking.objects.filter(customer__user=request.user)
    return Response({
        'profile': CustomerProfileSerializer(profile).data,
        'booking_histories': BookingSerializer(history, many=True).data,
    })


class CustomerProfileDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile."""

    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH', 'POST']:
            return CustomerProfileUpdateSerializer
        return CustomerProfileSerializer

    def get_object(self):
        return get_object_or_404(CustomerProfile, user=self.request.user)

    def post(self, request, *args, **kwargs):
        """Handle partial updates via POST."""
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """Handle full updates."""
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerProfileImageUpdateView(generics.UpdateAPIView):
    """Update the authenticated user's profile image."""

    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        return get_object_or_404(CustomerProfile, user=self.request.user)

    ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

    def post(self, request, *args, **kwargs):
        """Handle profile image upload."""
        profile = self.get_object()
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        image = request.FILES['image']
        if image.content_type not in self.ALLOWED_IMAGE_TYPES:
            return Response(
                {'error': 'Invalid image type. Allowed: JPEG, PNG, GIF, WebP'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if image.size > self.MAX_IMAGE_SIZE:
            return Response(
                {'error': 'Image too large. Maximum size is 5MB'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile.image = image
        profile.save()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_display_picture(request):
    """Update the user's display picture."""
    profile = get_object_or_404(CustomerProfile, user=request.user)
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST
        )
    uploaded = request.FILES['file']
    if uploaded.content_type not in ALLOWED_IMAGE_TYPES:
        return Response(
            {'error': 'Invalid image type. Allowed: JPEG, PNG, GIF, WebP'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if uploaded.size > MAX_IMAGE_SIZE:
        return Response(
            {'error': 'Image too large. Maximum size is 5MB'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    profile.image = uploaded
    profile.save()
    return Response(
        {'image_url': profile.image.url}, status=status.HTTP_200_OK
    )


# ---------------------------------------------------------------------------
# Search Views
# ---------------------------------------------------------------------------

@api_view(['GET'])
def search_locations(request):
    """Search locations by country, state, and type."""
    country = request.GET.get('country')
    states = request.GET.getlist('state')
    location_type = request.GET.get('type')

    state_queries = Q()
    for state in states:
        state_queries |= Q(state__icontains=state)

    locations = Locations.objects.filter(
        Q(country__iexact=country) & state_queries & Q(type__iexact=location_type)
    )
    return Response(LocationsSerializer(locations, many=True).data)


class SearchCountriesLocationsView(APIView):
    """Search locations by country code and place types."""

    def get(self, request):
        country = request.GET.get('country')
        places = request.GET.get('places', '')
        if not country or not places:
            return Response(
                {'error': 'country and places parameters are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        places_list = places.split(',')
        country_info = get_country_info(country)
        if not country_info:
            return Response(
                {'error': 'Invalid country code'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        country_name = country_info[0]
        locations = Locations.objects.filter(
            country__iexact=country_name, type__in=places_list
        )
        data = list(locations.values('title', 'state'))
        return Response({'locations': data}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Package Save/Unsave
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_package(request, package_id):
    """Save a package to the user's saved list."""
    try:
        package = Package.objects.get(package_id=package_id)
    except Package.DoesNotExist:
        return Response(
            {'error': 'Package not found'}, status=status.HTTP_404_NOT_FOUND
        )

    user = request.user
    if package in user.saved_packages.all():
        return Response(
            {'message': f'Package "{package.name}" is already saved'},
            status=status.HTTP_208_ALREADY_REPORTED,
        )
    user.saved_packages.add(package)
    return Response(
        {'message': f'Package "{package.name}" saved successfully'},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unsave_package(request, package_id):
    """Remove a package from the user's saved list."""
    try:
        package = Package.objects.get(package_id=package_id)
    except Package.DoesNotExist:
        return Response(
            {'error': 'Package not found'}, status=status.HTTP_404_NOT_FOUND
        )

    request.user.saved_packages.remove(package)
    return Response(
        {'message': f'Package "{package.name}" unsaved successfully'},
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_saved_packages(request):
    """Return the user's saved packages."""
    saved_packages = request.user.saved_packages.all()
    serializer = PackageSerializer(saved_packages, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Check Offer
# ---------------------------------------------------------------------------

class CheckOfferView(APIView):
    """Check pricing offers for a package based on guest counts."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pid):
        try:
            package = Package.objects.get(package_id=pid)
        except Package.DoesNotExist:
            return Response(
                {'error': 'Package not found'}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            adult = int(request.GET.get('adult', 0))
            children = int(request.GET.get('children', 0))
        except (ValueError, TypeError):
            return Response(
                {'error': 'adult and children must be integers'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not package.discount_price:
            return Response(
                {'error': 'No discount pricing available'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        offers = package.discount_price.split('-')
        offers = [offer.split(',') for offer in offers if len(offer.split(',')) >= 3]
        offers = [
            {
                'adult': int(offer[0]),
                'children': int(offer[1]),
                'price': int(offer[2]),
            }
            for offer in offers
        ]
        matching_offer = next(
            (
                offer for offer in offers
                if offer['adult'] >= adult and offer['children'] >= children
            ),
            None,
        )
        if matching_offer:
            return Response(matching_offer, status=status.HTTP_200_OK)
        return Response(
            {'error': 'No matching offer found'},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ---------------------------------------------------------------------------
# Booking Views
# ---------------------------------------------------------------------------

class BookPackageView(APIView):
    """Create a new booking for a package."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pid):
        try:
            package = Package.objects.get(package_id=pid)
        except Package.DoesNotExist:
            return Response(
                {'error': 'Package not found'}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.save(
                customer=request.user.customerprofile,
                package=package.package_id,
                booking_id=generate_booking_id(),
            )
            return Response(
                {'message': 'Booking successful', 'booking_id': booking.booking_id},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingViewSet(viewsets.ModelViewSet):
    """CRUD operations for bookings."""

    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'booking_id'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(customer__user=self.request.user)

    def perform_create(self, serializer):
        customer = CustomerProfile.objects.get(user=self.request.user)
        price = get_price(
            serializer.validated_data['package'],
            serializer.validated_data['adult'],
            serializer.validated_data['children'],
        )
        serializer.save(
            customer=customer,
            booking_id=generate_booking_id(),
            price=price,
        )


class CruiseBookingViewSet(viewsets.ModelViewSet):
    """CRUD operations for cruise bookings.

    Uses the PersonalisedBooking model with event_type automatically set to
    'cruise'. This matches the mobile app's "Plan Your Dream Event" cruise form
    which includes cruise_type, duration_hours, services, etc.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return PersonalisedBookingCreateSerializer
        return PersonalisedBookingSerializer

    def get_queryset(self):
        qs = PersonalisedBooking.objects.filter(event_type='cruise')
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, event_type='cruise')


# ---------------------------------------------------------------------------
# Invoice & Payment Views
# ---------------------------------------------------------------------------

class PreviewInvoiceView(APIView):
    """Preview an invoice by its ID."""

    permission_classes = [IsAuthenticated]

    def get(self, request, inv):
        invoice = get_object_or_404(Invoice, invoice_id=inv)
        if invoice.booking.customer.user != request.user and not request.user.is_staff:
            return Response(
                {'status': 'error', 'message': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MakePaymentView(APIView):
    """Record a payment for an invoice."""

    permission_classes = [IsAuthenticated]

    def post(self, request, inv):
        invoice = get_object_or_404(Invoice, invoice_id=inv)
        if invoice.booking.customer.user != request.user and not request.user.is_staff:
            return Response(
                {'status': 'error', 'message': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if invoice.paid:
            return Response(
                {'status': 'error', 'message': 'Invoice is already paid'},
                status=status.HTTP_409_CONFLICT,
            )
        Payment.objects.create(
            invoice=invoice,
            payment_id=generate_payment_id(),
            amount=invoice.subtotal,
            admin_fee=invoice.admin_fee,
            vat=invoice.tax_amount,
            total=invoice.total,
        )
        invoice.status = 'paid'
        invoice.paid = True
        invoice.save()
        return Response(
            {'status': 'success', 'message': 'Payment successful'},
            status=status.HTTP_200_OK,
        )


def create_package_invoice(booking, package):
    """Create an invoice for a booking and return the invoice number.

    Uses atomic transactions with retry logic to handle concurrent
    invoice number generation safely (invoice_id has a unique constraint).
    """
    tax = package.vat
    subtotal = booking.price
    items = json.dumps([
        [package.name, 1, 'package', str(subtotal), str(subtotal)]
    ])
    service_charge_percent = 0
    sc_amount = Decimal(service_charge_percent) * subtotal / 100
    tax_amount = Decimal(tax) * (subtotal + sc_amount) / 100
    grandtotal = subtotal + tax_amount + sc_amount

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with db_transaction.atomic():
                invoice_number = _next_invoice_number()
                Invoice.objects.create(
                    invoice_id=invoice_number,
                    booking=booking,
                    items=items,
                    subtotal=subtotal,
                    tax=tax,
                    tax_amount=tax_amount,
                    total=grandtotal,
                    admin_fee=sc_amount,
                    admin_percentage=service_charge_percent,
                )
                booking.status = 'invoiced'
                booking.invoiced = True
                booking.invoice_id = invoice_number
                booking.save()
                package.applications += 1
                package.save()
                return invoice_number
        except IntegrityError:
            if attempt == max_retries - 1:
                logger.exception(
                    "Failed to generate unique invoice number for booking %s after %d retries",
                    booking.booking_id, max_retries,
                )
                return None
            continue

    return None


def pay_invoice(inv):
    """Mark an invoice as paid and create the corresponding payment record."""
    invoice = Invoice.objects.get(invoice_id=inv)
    txn = generate_transaction_id()
    Payment.objects.create(
        invoice=invoice,
        transaction_id=txn,
        payment_id=generate_payment_id(),
        amount=Decimal(invoice.subtotal),
        vat=Decimal(invoice.tax_amount),
        total=Decimal(invoice.total),
        admin_fee=Decimal(invoice.admin_fee),
    )
    invoice.status = 'paid'
    invoice.paid = True
    invoice.transaction_id = txn
    invoice.save()

    booking = invoice.booking
    booking.status = 'paid'
    booking.save()


def _publish_invoice(url, payment_name):
    """Convert an invoice URL to PDF via PDFShift and save to disk.

    Internal helper — not a view. Uses MEDIA_ROOT for file storage.
    """
    response = requests.post(
        'https://api.pdfshift.io/v3/convert/pdf',
        auth=('api', settings.PDFSHIFT_API_KEY),
        json={
            'source': url,
            'landscape': False,
            'use_print': False,
        },
        timeout=30,
    )
    response.raise_for_status()
    invoice_dir = os.path.join(settings.MEDIA_ROOT, 'customer', 'invoices')
    os.makedirs(invoice_dir, exist_ok=True)
    safe_name = os.path.basename(payment_name).replace(' ', '_')
    file_path = os.path.join(invoice_dir, f'{safe_name}.pdf')
    # Ensure the resolved path is within the invoice directory
    if not os.path.realpath(file_path).startswith(os.path.realpath(invoice_dir)):
        raise ValueError("Invalid file path")
    with open(file_path, 'wb') as f:
        f.write(response.content)
    return file_path


def prepare_invoice(booking, package):
    """Create, pay, and email an invoice for a completed booking."""
    try:
        invoice_number = create_package_invoice(booking, package)
        if not invoice_number:
            return {'status': 'error', 'message': 'Failed to create invoice'}

        pay_invoice(invoice_number)
        package.submissions += 1
        package.bookings.add(booking)
        package.save()

        invoice_url = f'{settings.SITE_URL}/print-invoice/{invoice_number}/'
        pdf_path = _publish_invoice(invoice_url, booking.booking_id)
        customer_name = f'{booking.lastname} {booking.firstname}'
        send_invoice_email(booking.email, customer_name, invoice_number, pdf_path)

        notify_payment_received(booking, booking.price, booking.payment_method or 'stripe')
        notify_booking_confirmed(booking)

        return {'status': 'success', 'message': 'Invoice created'}
    except Exception:
        logger.exception("Failed to prepare invoice for booking %s", booking.booking_id)
        return {'status': 'error', 'message': 'Failed to prepare invoice'}


# ---------------------------------------------------------------------------
# Booking Payment & Confirmation
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pay_booking(request, booking_id, mode='wallet'):
    """Process payment for a booking via wallet, Stripe checkout, or split (wallet + Stripe).

    Modes:
        wallet: Full payment from wallet balance.
        stripe: Full payment via Stripe Checkout.
        split:  Deducts wallet balance first, then charges the remainder via Stripe.
                If wallet covers the full amount, behaves like wallet mode.
                If wallet is empty, returns an error (use stripe mode instead).
    """
    try:
        booking = get_object_or_404(
            Booking, booking_id=booking_id, customer__user=request.user
        )
        if booking.status == 'paid':
            return Response(
                {'status': 'error', 'message': 'Booking is already paid'},
                status=status.HTTP_409_CONFLICT,
            )
        if booking.status != 'pending':
            return Response(
                {'status': 'error', 'message': f'Booking status is {booking.status}, expected pending'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        package = Package.objects.get(package_id=booking.package)

        if mode == 'wallet':
            try:
                wallet = Wallet.objects.get(user=request.user)
            except Wallet.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': 'Wallet not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            withdraw = wallet.withdraw(booking.price)
            withdraw.description = 'Full wallet payment for booking'
            withdraw.reference = booking.booking_id
            withdraw.save()
            booking.status = 'paid'
            booking.payment_status = 'paid'
            booking.payment_method = 'wallet'
            booking.wallet_amount_paid = booking.price
            booking.wallet_transaction_id = str(withdraw.id)
            booking.checkout_session_id = 'wallet'
            booking.save()
            return Response({
                'status': 'success',
                'booking_id': booking.booking_id,
                'mode': 'wallet',
            })

        elif mode == 'split':
            try:
                wallet = Wallet.objects.get(user=request.user)
            except Wallet.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': 'Wallet not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if wallet.balance <= 0:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Wallet has no balance. Use stripe mode instead.',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            wallet_amount = min(wallet.balance, booking.price)
            stripe_amount = booking.price - wallet_amount

            if stripe_amount <= 0:
                # Wallet covers the full amount — process as wallet payment
                withdraw = wallet.withdraw(booking.price)
                withdraw.description = 'Full wallet payment for booking'
                withdraw.reference = booking.booking_id
                withdraw.save()
                booking.status = 'paid'
                booking.payment_status = 'paid'
                booking.payment_method = 'wallet'
                booking.wallet_amount_paid = booking.price
                booking.wallet_transaction_id = str(withdraw.id)
                booking.checkout_session_id = 'wallet'
                booking.save()
                return Response({
                    'status': 'success',
                    'booking_id': booking.booking_id,
                    'mode': 'wallet',
                    'message': 'Wallet balance covered the full amount.',
                })

            # Deduct wallet portion
            withdraw = wallet.withdraw(wallet_amount)
            withdraw.description = (
                f'Split payment ({wallet_amount} from wallet, '
                f'{stripe_amount} via Stripe) for booking {booking.booking_id}'
            )
            withdraw.reference = booking.booking_id
            withdraw.save()

            # Create Stripe checkout session for the remaining amount + tax
            tax_on_full_price = int(package.vat * booking.price)
            session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': (
                                    f"{package.name} — remaining balance "
                                    f"(wallet covered ${wallet_amount:.2f})"
                                ),
                                'images': [f'{package.main_image.url}'],
                            },
                            'unit_amount': int(stripe_amount * 100),
                        },
                        'quantity': 1,
                    },
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"{package.vat}% Tax",
                            },
                            'unit_amount': tax_on_full_price,
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                customer_email=request.user.email,
                success_url=f'{settings.SITE_URL}/payment/success',
                cancel_url=f'{settings.SITE_URL}/payment/cancel',
                metadata={
                    'booking_id': booking.booking_id,
                    'type': 'split_booking_payment',
                    'wallet_amount': str(wallet_amount),
                    'stripe_amount': str(stripe_amount),
                },
            )

            booking.checkout_session_id = session.id
            booking.payment_method = 'split'
            booking.wallet_amount_paid = wallet_amount
            booking.stripe_amount_due = stripe_amount
            booking.wallet_transaction_id = str(withdraw.id)
            booking.save()

            return Response({
                'status': 'success',
                'checkout_url': session.url,
                'session_id': session.id,
                'mode': 'split',
                'wallet_amount': str(wallet_amount),
                'stripe_amount': str(stripe_amount),
                'booking_id': booking.booking_id,
            })

        else:
            # Default: full Stripe checkout
            session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': (
                                    f"{package.name} with {booking.adult} adult "
                                    f"and {booking.children} children"
                                ),
                                'images': [f'{package.main_image.url}'],
                            },
                            'unit_amount': int(booking.price * 100),
                        },
                        'quantity': 1,
                    },
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"{package.vat}% Tax",
                            },
                            'unit_amount': int(package.vat * booking.price),
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                customer_email=request.user.email,
                success_url=f'{settings.SITE_URL}/payment/success',
                cancel_url=f'{settings.SITE_URL}/payment/cancel',
                metadata={
                    'booking_id': booking.booking_id,
                    'type': 'booking_payment',
                },
            )
            booking.checkout_session_id = session.id
            booking.payment_method = 'stripe'
            booking.stripe_amount_due = booking.price
            booking.save()
            return Response({
                'status': 'success',
                'checkout_url': session.url,
                'session_id': session.id,
                'mode': 'stripe',
                'booking_id': booking.booking_id,
            })

    except ValueError:
        return Response(
            {'status': 'error', 'message': 'Invalid payment request'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        logger.exception("Error processing payment for booking %s", booking_id)
        return Response(
            {'status': 'error', 'message': 'An error occurred while processing your payment'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_complete(request, booking_id):
    """Handle booking completion after Stripe checkout redirect.

    This is the endpoint the frontend hits after Stripe redirects back
    to the success URL. It verifies the Stripe session and processes
    the invoice pipeline.
    """
    booking = get_object_or_404(
        Booking, booking_id=booking_id, customer__user=request.user
    )

    if booking.status == 'paid':
        return Response(
            {'status': 'error', 'message': 'Booking already completed'},
            status=status.HTTP_409_CONFLICT,
        )

    if not booking.checkout_session_id:
        return Response(
            {'status': 'error', 'message': 'No checkout session found'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        session = stripe.checkout.Session.retrieve(booking.checkout_session_id)
    except stripe.error.InvalidRequestError:
        return Response(
            {'status': 'error', 'message': 'Invalid checkout session'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if session.payment_status != 'paid':
        return Response(
            {'status': 'error', 'message': 'Payment not completed'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    package = get_object_or_404(Package, package_id=booking.package)

    booking.payment_status = 'paid'
    booking.save()

    result = prepare_invoice(booking, package)
    if result.get('status') == 'success':
        booking.status = 'paid'
        booking.save()
        return Response({
            'status': 'success',
            'message': 'Payment processed and invoice created',
            'booking_id': booking.booking_id,
        })

    return Response(
        {'status': 'error', 'message': result.get('message', 'Invoice preparation failed')},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_booking(request):
    """Confirm a booking after payment (wallet, Stripe, or split).

    Request body:
        identifier: booking_id (for wallet/split) or session_id (for stripe)
        mode: 'wallet', 'stripe', or 'split'
    """
    identifier = request.data.get('identifier')
    mode = request.data.get('mode')

    if not identifier or not mode:
        return Response(
            {'status': 'error', 'message': 'identifier and mode are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking = None
    identifier = identifier.strip()

    if mode == 'wallet':
        booking = get_object_or_404(
            Booking,
            booking_id=identifier,
            customer__user=request.user,
            checkout_session_id__isnull=False,
        )
        try:
            Transaction.objects.get(
                reference=booking.booking_id,
                transaction_type='withdrawal',
                status='completed',
            )
        except Transaction.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Wallet transaction not found'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    elif mode == 'split':
        # For split: identifier is the booking_id
        booking = get_object_or_404(
            Booking,
            booking_id=identifier,
            customer__user=request.user,
            payment_method='split',
        )

        # Verify wallet transaction exists
        try:
            Transaction.objects.get(
                reference=booking.booking_id,
                transaction_type='withdrawal',
                status='completed',
            )
        except Transaction.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Wallet transaction not found for split payment'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify Stripe payment
        if not booking.checkout_session_id:
            return Response(
                {'status': 'error', 'message': 'No Stripe checkout session found for split payment'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            session = stripe.checkout.Session.retrieve(booking.checkout_session_id)
            if session.payment_status != 'paid':
                return Response(
                    {'status': 'error', 'message': 'Stripe portion of split payment not completed'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except stripe.error.InvalidRequestError:
            return Response(
                {'status': 'error', 'message': 'Invalid checkout session'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    else:
        # Stripe mode: identifier is the session_id
        try:
            session = stripe.checkout.Session.retrieve(identifier)
            if session.payment_status != 'paid':
                return Response(
                    {'status': 'error', 'message': 'Payment not completed'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            booking = get_object_or_404(
                Booking,
                customer__user=request.user,
                checkout_session_id=identifier,
            )
        except stripe.error.InvalidRequestError:
            return Response(
                {'status': 'error', 'message': 'Invalid checkout session'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    package = get_object_or_404(Package, package_id=booking.package)

    if package.bookings.filter(id=booking.id).exists() and booking.status == 'paid':
        return Response(
            {'status': 'error', 'message': 'Booking already completed for this package'},
            status=status.HTTP_409_CONFLICT,
        )

    booking.payment_status = 'paid'
    booking.save()

    result = prepare_invoice(booking, package)
    if result.get('status') == 'success':
        booking.status = 'paid'
        booking.save()
        return Response({
            'status': 'success',
            'booking_id': booking.booking_id,
            'mode': mode,
        })

    return Response(
        {'status': 'error', 'message': result.get('message', 'Invoice preparation failed')},
        status=status.HTTP_400_BAD_REQUEST,
    )


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

@api_view(['POST'])
def contact_submit(request):
    """Submit a contact form message."""
    serializer = ContactSerializer(data=request.data)
    if serializer.is_valid():
        try:
            serializer.save()
        except Exception:
            logger.exception("Error saving contact form")
            return Response(
                {'status': 'error', 'message': 'Failed to submit your message. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            send_contact_email(serializer.validated_data)
        except Exception:
            logger.exception("Failed to send contact notification email")
        return Response(
            {
                'status': 'success',
                'message': (
                    'Your message has been sent successfully. '
                    'We will contact you soon.'
                ),
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {
            'status': 'error',
            'message': 'Invalid data provided',
            'errors': serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


# ---------------------------------------------------------------------------
# Booking Cancellation & Modification
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    """Cancel a booking and process refund based on cancellation policy.

    Policy:
        7+ days before travel date  → full refund
        3-7 days before             → 50% refund
        <3 days before              → no refund
        Already cancelled/paid-out  → rejected
    """
    booking = get_object_or_404(
        Booking, booking_id=booking_id, customer__user=request.user
    )

    if booking.status == 'cancelled':
        return Response(
            {'status': 'error', 'message': 'Booking is already cancelled'},
            status=status.HTTP_409_CONFLICT,
        )

    if booking.status not in ('pending', 'paid', 'invoiced'):
        return Response(
            {'status': 'error', 'message': f'Cannot cancel a booking with status "{booking.status}"'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CancelBookingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    refund_amount = Decimal('0.00')
    total_paid = booking.wallet_amount_paid + booking.stripe_amount_due

    if booking.status in ('paid', 'invoiced') and total_paid > 0:
        days_until_travel = (booking.datefrom - timezone.now().date()).days
        if days_until_travel >= 7:
            refund_amount = total_paid
        elif days_until_travel >= 3:
            refund_amount = (total_paid * Decimal('0.50')).quantize(Decimal('0.01'))
        # < 3 days: no refund

    booking.status = 'cancelled'
    booking.cancelled_at = timezone.now()
    booking.cancellation_reason = serializer.validated_data.get('reason', '')
    booking.refund_amount = refund_amount
    booking.refund_status = 'pending' if refund_amount > 0 else 'denied'
    booking.save()

    # Process wallet refund
    if refund_amount > 0:
        try:
            wallet = Wallet.objects.get(user=request.user)
            refund_txn = wallet.deposit(refund_amount)
            refund_txn.description = f'Refund for cancelled booking {booking.booking_id}'
            refund_txn.reference = booking.booking_id
            refund_txn.save()
            booking.refund_status = 'processed'
            booking.save()
            notify_refund_processed(booking, refund_amount)
        except Wallet.DoesNotExist:
            logger.warning("No wallet found for refund on booking %s", booking.booking_id)

    notify_booking_cancelled(booking, refund_amount)

    return Response({
        'status': 'success',
        'message': 'Booking cancelled',
        'booking_id': booking.booking_id,
        'refund_amount': str(refund_amount),
        'refund_status': booking.refund_status,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def modify_booking(request, booking_id):
    """Modify a pending booking (dates, guest counts). Price is recalculated."""
    booking = get_object_or_404(
        Booking, booking_id=booking_id, customer__user=request.user
    )

    if booking.status != 'pending':
        return Response(
            {'status': 'error', 'message': 'Only pending bookings can be modified'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ModifyBookingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if 'datefrom' in data:
        booking.datefrom = data['datefrom']
    if 'dateto' in data:
        booking.dateto = data['dateto']
    if 'adult' in data:
        booking.adult = data['adult']
    if 'children' in data:
        booking.children = data['children']
    if 'guests' in data:
        booking.guests = data['guests']

    if booking.datefrom and booking.dateto:
        booking.duration = (booking.dateto - booking.datefrom).days

    # Recalculate price if guest counts changed
    if 'adult' in data or 'children' in data:
        new_price = get_price(booking.package, booking.adult, booking.children)
        if new_price > 0:
            booking.price = new_price - booking.discount_amount

    booking.save()

    return Response({
        'status': 'success',
        'message': 'Booking updated',
        'booking': BookingSerializer(booking).data,
    })


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
def package_reviews(request, pid):
    """List reviews for a package (GET) or create a review (POST)."""
    package = get_object_or_404(Package, package_id=pid)

    if request.method == 'GET':
        reviews = Review.objects.filter(package=package)
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
        return Response({
            'reviews': ReviewSerializer(reviews, many=True).data,
            'count': reviews.count(),
            'average_rating': round(avg_rating, 2) if avg_rating else None,
        })

    # POST: create a review
    if not request.user.is_authenticated:
        return Response(
            {'status': 'error', 'message': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Verify user has a completed booking for this package
    has_booking = Booking.objects.filter(
        customer__user=request.user,
        package=package.package_id,
        status='paid',
    ).exists()
    if not has_booking:
        return Response(
            {'status': 'error', 'message': 'You can only review packages you have booked'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if Review.objects.filter(user=request.user, package=package).exists():
        return Response(
            {'status': 'error', 'message': 'You have already reviewed this package'},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = ReviewCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    review = serializer.save(user=request.user, package=package)
    return Response(
        {'status': 'success', 'review': ReviewSerializer(review).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_detail(request, review_id):
    """Update or delete the authenticated user's review."""
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == 'DELETE':
        review.delete()
        return Response(
            {'status': 'success', 'message': 'Review deleted'},
            status=status.HTTP_200_OK,
        )

    serializer = ReviewCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    review.rating = serializer.validated_data['rating']
    review.comment = serializer.validated_data.get('comment', '')
    review.save()
    return Response(
        {'status': 'success', 'review': ReviewSerializer(review).data},
    )


# ---------------------------------------------------------------------------
# Promo Code
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_promo_code(request, booking_id):
    """Validate and apply a promo code to a pending booking.

    Updates the booking price with the discount and records the promo code.
    """
    booking = get_object_or_404(
        Booking, booking_id=booking_id, customer__user=request.user
    )

    if booking.status != 'pending':
        return Response(
            {'status': 'error', 'message': 'Promo codes can only be applied to pending bookings'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if booking.promo_code:
        return Response(
            {'status': 'error', 'message': 'A promo code is already applied to this booking'},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = PromoCodeApplySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        promo = PromoCode.objects.get(code__iexact=serializer.validated_data['code'])
    except PromoCode.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Invalid promo code'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not promo.is_valid():
        return Response(
            {'status': 'error', 'message': 'This promo code has expired or reached its usage limit'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    original_price = booking.price + booking.discount_amount  # undo any previous discount
    discount = promo.calculate_discount(original_price)

    if discount <= 0:
        return Response(
            {'status': 'error', 'message': f'Minimum order amount of {promo.min_order_amount} not met'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking.promo_code = promo
    booking.discount_amount = discount
    booking.price = original_price - discount
    booking.save()

    promo.current_uses += 1
    promo.save()

    return Response({
        'status': 'success',
        'message': f'Promo code applied. You save {discount}!',
        'original_price': str(original_price),
        'discount': str(discount),
        'new_price': str(booking.price),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_promo_code(request, booking_id):
    """Remove an applied promo code from a pending booking."""
    booking = get_object_or_404(
        Booking, booking_id=booking_id, customer__user=request.user
    )

    if booking.status != 'pending':
        return Response(
            {'status': 'error', 'message': 'Cannot modify a non-pending booking'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not booking.promo_code:
        return Response(
            {'status': 'error', 'message': 'No promo code applied to this booking'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    promo = booking.promo_code
    booking.price = booking.price + booking.discount_amount
    booking.discount_amount = Decimal('0.00')
    booking.promo_code = None
    booking.save()

    promo.current_uses = max(0, promo.current_uses - 1)
    promo.save()

    return Response({
        'status': 'success',
        'message': 'Promo code removed',
        'price': str(booking.price),
    })


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """List and manage the authenticated user's notifications."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Return the count of unread notifications."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'success', 'message': 'Notification marked as read'})

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({
            'status': 'success',
            'message': f'{updated} notifications marked as read',
        })


# ---------------------------------------------------------------------------
# Support Tickets
# ---------------------------------------------------------------------------

class SupportTicketViewSet(viewsets.ModelViewSet):
    """CRUD operations for support tickets with messaging."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SupportTicketCreateSerializer
        return SupportTicketSerializer

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create a support ticket with an initial message."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket = SupportTicket.objects.create(
            user=request.user,
            subject=serializer.validated_data['subject'],
            priority=serializer.validated_data.get('priority', 'medium'),
        )
        SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=serializer.validated_data['message'],
        )

        return Response(
            SupportTicketSerializer(ticket).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """Add a reply message to a support ticket."""
        ticket = self.get_object()

        if ticket.status == 'closed':
            return Response(
                {'status': 'error', 'message': 'Cannot reply to a closed ticket'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SupportReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=serializer.validated_data['message'],
        )
        ticket.save()  # bump updated_at

        return Response(
            SupportTicketSerializer(ticket).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a support ticket."""
        ticket = self.get_object()
        ticket.status = 'closed'
        ticket.save()
        return Response({'status': 'success', 'message': 'Ticket closed'})


# ---------------------------------------------------------------------------
# Invoice Download
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_invoice(request, invoice_id):
    """Return the invoice PDF download URL (or regenerate if missing)."""
    invoice = get_object_or_404(Invoice, invoice_id=invoice_id)

    # Verify user owns this invoice
    if invoice.booking.customer.user != request.user:
        return Response(
            {'status': 'error', 'message': 'Not authorized'},
            status=status.HTTP_403_FORBIDDEN,
        )

    invoice_dir = os.path.join(settings.MEDIA_ROOT, 'customer', 'invoices')
    safe_name = invoice.booking.booking_id.replace(' ', '_')
    pdf_path = os.path.join(invoice_dir, f'{safe_name}.pdf')

    if not os.path.exists(pdf_path):
        # Regenerate the PDF
        try:
            invoice_url = f'{settings.SITE_URL}/print-invoice/{invoice_id}/'
            pdf_path = _publish_invoice(invoice_url, invoice.booking.booking_id)
        except Exception:
            logger.exception("Failed to regenerate invoice PDF for %s", invoice_id)
            return Response(
                {'status': 'error', 'message': 'Invoice PDF not available'},
                status=status.HTTP_404_NOT_FOUND,
            )

    pdf_url = f'{settings.MEDIA_URL}customer/invoices/{safe_name}.pdf'
    return Response({
        'status': 'success',
        'invoice_id': invoice_id,
        'download_url': pdf_url,
    })


# ---------------------------------------------------------------------------
# Event ViewSet
# ---------------------------------------------------------------------------

class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for events, filterable by country."""

    queryset = Event.objects.filter(status='active').order_by('-id')
    serializer_class = EventSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country=country)
        return queryset


# ---------------------------------------------------------------------------
# Personalised Bookings
# ---------------------------------------------------------------------------

class PersonalisedBookingViewSet(viewsets.ModelViewSet):
    """CRUD for personalised booking requests.

    Authenticated users can create and view their own requests.
    Staff can view all requests and update status/admin_notes.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return PersonalisedBookingCreateSerializer
        return PersonalisedBookingSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return PersonalisedBooking.objects.all()
        return PersonalisedBooking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ---------------------------------------------------------------------------
# Carousel
# ---------------------------------------------------------------------------

class CarouselViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for active carousel items (public).

    Query params:
        category: filter by category (personalise, cruise, packages)
    """

    serializer_class = CarouselSerializer
    queryset = Carousel.objects.filter(is_active=True)

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs


# ---------------------------------------------------------------------------
# Print Invoice (HTML view for PDFShift rendering)
# ---------------------------------------------------------------------------

def print_invoice(request, invoice_id):
    """Render an invoice as HTML for PDF generation via PDFShift.

    This is NOT an API endpoint — it returns an HTML page that PDFShift
    fetches and converts to PDF.
    """
    from django.shortcuts import render

    invoice = get_object_or_404(Invoice, invoice_id=invoice_id)
    booking = invoice.booking

    # Parse items JSON → list of lists
    try:
        items = json.loads(invoice.items)
    except (json.JSONDecodeError, TypeError):
        items = []

    # Pre-parse destinations so template doesn't need custom tags
    destinations = []
    if booking.destinations:
        destinations = [d.strip() for d in booking.destinations.split('-') if d.strip()]
        if not destinations:
            destinations = [d.strip() for d in booking.destinations.split(',') if d.strip()]

    # Billing info from customer profile (if exists)
    customer = getattr(booking, 'customer', None)
    context = {
        'customer': f'{booking.lastname} {booking.firstname}',
        'invoice_number': invoice.invoice_id,
        'phone': booking.phone,
        'email': booking.email,
        'date': invoice.created_at,
        'booking': booking,
        'items': items,
        'destinations': destinations,
        'billing_address': getattr(customer, 'address', booking.address) if customer else booking.address,
        'billing_city': getattr(customer, 'city', booking.city) if customer else booking.city,
        'billing_state': getattr(booking, 'state', ''),
        'billing_country': getattr(customer, 'country', booking.country) if customer else booking.country,
        'subtotal': invoice.subtotal,
        'scp': invoice.admin_percentage,
        'sc_amount': invoice.admin_fee,
        'tax': invoice.tax,
        'tax_amount': invoice.tax_amount,
        'grandtotal': invoice.total,
    }
    return render(request, 'index/print-invoice.html', context)
