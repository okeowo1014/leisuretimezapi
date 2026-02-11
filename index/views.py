"""
API views for the Leisuretimez travel booking platform.

Handles packages, bookings, invoices, payments, profiles, contacts, and search.
"""

import json
import logging
import uuid
from decimal import Decimal

import requests
import stripe
from django.conf import settings
from django.db import models
from django.db.models import BooleanField, Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from index.countrylist import get_country_info
from index.utils import send_contact_email, send_invoice_email

from .models import (
    Booking, CustomerProfile, Destination, Event, GuestImage, Invoice,
    Locations, Package, PackageImage, Payment, Transaction, Wallet,
)
from .serializers import (
    BookingSerializer, ContactSerializer, CustomerProfileSerializer,
    CustomerProfileUpdateSerializer, DestinationSerializer, EventSerializer,
    GuestImageSerializer, InvoiceSerializer, LocationsSerializer,
    PackageSerializer, PackageImageSerializer,
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


def get_invoice_number(last_invoice_id):
    """Generate the next sequential invoice number."""
    current_num = int(last_invoice_id.split('-')[1])
    return f'INV-{str(current_num + 1).zfill(6)}'


# ---------------------------------------------------------------------------
# Homepage & Package Views
# ---------------------------------------------------------------------------

@api_view(['GET'])
def index(request):
    """Return homepage data: active packages, destinations, and events."""
    packages = _get_packages_queryset(request.user)
    destinations = Destination.objects.filter(status='active')
    events = Event.objects.filter(status='active')
    return Response({
        'packages': PackageSerializer(packages, many=True).data,
        'destinations': DestinationSerializer(destinations, many=True).data,
        'events': EventSerializer(events, many=True).data,
    })


@api_view(['GET'])
def package_list(request):
    """Return all active packages with saved status."""
    packages = _get_packages_queryset(request.user)
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

    def post(self, request, *args, **kwargs):
        """Handle profile image upload."""
        profile = self.get_object()
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile.image = request.FILES['image']
        profile.save()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_display_picture(request):
    """Update the user's display picture."""
    profile = get_object_or_404(CustomerProfile, user=request.user)
    if 'file' in request.FILES:
        profile.image = request.FILES['file']
        profile.save()
        return Response(
            {'image_url': profile.image.url}, status=status.HTTP_200_OK
        )
    return Response(
        {'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST
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

        adult = int(request.GET.get('adult', 0))
        children = int(request.GET.get('children', 0))

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
            serializer.save(
                customer=request.user.customerprofile,
                package=package.package_id,
                booking_id=generate_booking_id(),
            )
            return Response(
                {'message': 'Booking successful'}, status=status.HTTP_201_CREATED
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
    """CRUD operations for cruise bookings."""

    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'booking_id'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(customer__user=self.request.user)

    def perform_create(self, serializer):
        customer = CustomerProfile.objects.get(user=self.request.user)
        serializer.save(
            customer=customer,
            booking_id=generate_booking_id(),
        )


# ---------------------------------------------------------------------------
# Invoice & Payment Views
# ---------------------------------------------------------------------------

class PreviewInvoiceView(APIView):
    """Preview an invoice by its ID."""

    permission_classes = [IsAuthenticated]

    def get(self, request, inv):
        invoice = get_object_or_404(Invoice, invoice_id=inv)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MakePaymentView(APIView):
    """Record a payment for an invoice."""

    permission_classes = [IsAuthenticated]

    def post(self, request, inv):
        invoice = get_object_or_404(Invoice, invoice_id=inv)
        Payment.objects.create(
            invoice=invoice,
            payment_id=generate_payment_id(),
            amount=invoice.subtotal,
            admin_fee=invoice.admin_fee,
            vat=invoice.tax_amount,
            total=invoice.total,
        )
        invoice.status = 'paid'
        invoice.save()
        return Response(
            {'message': 'Payment successful'}, status=status.HTTP_200_OK
        )


def create_package_invoice(booking, package):
    """Create an invoice for a booking and return the invoice number."""
    try:
        invoice_number = get_invoice_number(
            Invoice.objects.latest('invoice_id').invoice_id
        )
    except Invoice.DoesNotExist:
        invoice_number = 'INV-000001'

    tax = package.vat
    names = [package.name]
    quantity = [1]
    units = ['package']
    prices = [booking.price]
    unitprice = [
        Decimal(qty) * Decimal(prc) for qty, prc in zip(quantity, prices)
    ]
    items = json.dumps([
        [name, qty, unit, str(price), str(uprc)]
        for name, qty, unit, price, uprc
        in zip(names, quantity, units, prices, unitprice)
    ])
    subtotal = sum(
        Decimal(qty) * Decimal(price)
        for qty, price in zip(quantity, prices)
    )
    service_charge_percent = 0
    sc_amount = Decimal(service_charge_percent) * subtotal / 100
    tax_amount = Decimal(tax) * (subtotal + sc_amount) / 100
    grandtotal = subtotal + tax_amount + sc_amount

    try:
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
    except Exception:
        logger.exception("Failed to create invoice for booking %s", booking.booking_id)
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
    invoice.booking.status = 'paid'
    invoice.paid = True
    invoice.transaction_id = txn
    invoice.save()


def publish_invoice(url, payment_name):
    """Convert an invoice URL to PDF via PDFShift and save to disk."""
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
    file_name = (
        f"/home/findepbl/leisuretimezmedia/customer/invoices/{payment_name}.pdf"
        .replace(' ', '_')
    )
    with open(file_name, 'wb') as f:
        f.write(response.content)
    return file_name


def prepare_invoice(booking, package):
    """Create, pay, and email an invoice for a completed booking."""
    try:
        invoice_number = create_package_invoice(booking, package)
        if invoice_number:
            pay_invoice(invoice_number)
            package.submissions += 1
            package.bookings.add(booking)
            package.save()
            fn = publish_invoice(
                f'https://www.leisuretimez.com/print-invoice/{invoice_number}/',
                booking.booking_id,
            )
            customer_name = (
                f'{booking.customer.user.lastname} {booking.customer.user.firstname}'
            )
            send_invoice_email(
                booking.customer.user.email, customer_name, invoice_number, fn
            )
            return {'status': 'successful', 'message': 'Invoice created'}
        return {'status': 'failed', 'message': 'Failed to create invoice'}
    except Exception as e:
        logger.exception("Failed to prepare invoice for booking %s", booking.booking_id)
        return {'status': 'failed', 'message': str(e)}


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
                {'status': 'failed', 'message': 'Already paid'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if booking.status != 'pending':
            return Response(
                {'status': 'failed', 'message': f'Booking status is {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        package = Package.objects.get(package_id=booking.package)

        if mode == 'wallet':
            wallet = Wallet.objects.get(user=request.user)
            withdraw = wallet.withdraw(booking.price)
            withdraw.description = 'Payment for booking'
            withdraw.reference = booking.booking_id
            withdraw.save()
            booking.status = 'paid'
            booking.payment_status = 'paid'
            booking.payment_method = 'wallet'
            booking.wallet_amount_paid = booking.price
            booking.checkout_session_id = 'wallet'
            booking.save()
            return Response({
                'status': 'successful',
                'booking_id': booking.booking_id,
                'mode': 'wallet',
            })

        elif mode == 'split':
            try:
                wallet = Wallet.objects.get(user=request.user)
            except Wallet.DoesNotExist:
                return Response(
                    {'status': 'failed', 'message': 'Wallet not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if wallet.balance <= 0:
                return Response(
                    {
                        'status': 'failed',
                        'message': 'Wallet has no balance. Use stripe mode instead.',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            wallet_amount = min(wallet.balance, booking.price)
            stripe_amount = booking.price - wallet_amount

            if stripe_amount <= 0:
                # Wallet covers the full amount — process as wallet payment
                withdraw = wallet.withdraw(booking.price)
                withdraw.description = 'Payment for booking'
                withdraw.reference = booking.booking_id
                withdraw.save()
                booking.status = 'paid'
                booking.payment_status = 'paid'
                booking.payment_method = 'wallet'
                booking.wallet_amount_paid = booking.price
                booking.checkout_session_id = 'wallet'
                booking.save()
                return Response({
                    'status': 'successful',
                    'booking_id': booking.booking_id,
                    'mode': 'wallet',
                    'message': 'Wallet balance covered the full amount.',
                })

            # Deduct wallet portion
            withdraw = wallet.withdraw(wallet_amount)
            withdraw.description = (
                f'Split payment for booking {booking.booking_id}'
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
            booking.save()

            return Response({
                'status': 'successful',
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
                'status': 'successful',
                'checkout_url': session.url,
                'session_id': session.id,
                'mode': 'checkout',
            })

    except ValueError as e:
        return Response(
            {'status': 'failed', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception("Error processing payment for booking %s", booking_id)
        return Response(
            {'status': 'failed', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_complete(request, booking_id):
    """Handle booking completion after Stripe checkout."""
    try:
        booking = get_object_or_404(Booking, booking_id=booking_id)
        if not booking.checkout_session_id:
            return Response(
                {'error': 'No checkout session found'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = stripe.checkout.Session.retrieve(booking.checkout_session_id)
        if session.payment_status != 'paid':
            return Response(
                {'error': 'Payment not completed'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.payment_status = 'paid'
        booking.status = 'confirmed'
        booking.save()

        package = Package.objects.get(package_id=booking.package)
        invoice_number = create_package_invoice(booking, package)
        if invoice_number:
            package.submissions += 1
            package.bookings.add(booking)
            package.save()

            invoice_url = request.build_absolute_uri(
                f'/print-invoice/{invoice_number}/'
            )
            pdf_path = publish_invoice(invoice_url, booking.booking_id)
            customer_name = f'{booking.firstname} {booking.lastname}'
            send_invoice_email(
                booking.email, customer_name, invoice_number, pdf_path
            )
            return Response({
                'status': 'success',
                'message': 'Payment processed successfully',
            })

        return Response(
            {'error': 'Failed to create invoice'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        logger.exception("Error completing booking %s", booking_id)
        return Response(
            {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
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
            {'error': 'identifier and mode are required.'},
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
                {'error': 'Transaction not found'},
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
                {'error': 'Wallet transaction not found for split payment'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify Stripe payment
        if not booking.checkout_session_id:
            return Response(
                {'error': 'No Stripe checkout session found for split payment'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            session = stripe.checkout.Session.retrieve(booking.checkout_session_id)
            if session.payment_status != 'paid':
                return Response(
                    {
                        'status': 'failed',
                        'error': 'Stripe portion of split payment not completed',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except stripe.error.InvalidRequestError as e:
            return Response(
                {'status': 'failed', 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    else:
        # Stripe mode: identifier is the session_id
        try:
            session = stripe.checkout.Session.retrieve(identifier)
            if session.payment_status != 'paid':
                return Response(
                    {'status': 'failed', 'error': 'Payment not found'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            booking = get_object_or_404(
                Booking,
                customer__user=request.user,
                checkout_session_id=identifier,
            )
        except stripe.error.InvalidRequestError as e:
            return Response(
                {'status': 'failed', 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    package = get_object_or_404(Package, package_id=booking.package)

    if package.bookings.filter(id=booking.id).exists() and booking.status == 'paid':
        return Response(
            {'error': 'You have already booked this package.'},
            status=status.HTTP_409_CONFLICT,
        )

    booking.payment_status = 'paid'
    booking.save()

    prepared_invoice = prepare_invoice(booking, package)
    if prepared_invoice.get('status') == 'successful':
        booking.status = 'paid'
        booking.save()
        return Response({
            'status': 'successful',
            'booking_id': booking.booking_id,
            'mode': mode,
        })

    return Response(
        {
            'status': 'failed',
            'error': prepared_invoice.get('message', 'Invoice preparation failed.'),
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_booking_payment(request):
    """Verify a Stripe checkout session for a booking payment."""
    session_id = request.data.get('session_id')
    if not session_id:
        return Response(
            {'error': 'Session ID not provided.'}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status != 'paid':
            return Response(
                {'status': 'failed', 'error': 'Payment not found'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking = get_object_or_404(
            Booking,
            customer__user=request.user,
            checkout_session_id=session_id,
        )
        package = Package.objects.get(package_id=booking.package)

        prepared_invoice = prepare_invoice(booking, package)
        if prepared_invoice['status'] == 'successful':
            booking.status = 'paid'
            booking.payment_status = 'paid'
            booking.save()
            return Response({
                'status': 'successful',
                'booking_id': booking.booking_id,
                'mode': booking.checkout_session_id,
            })
        return Response(
            {'status': 'failed', 'error': prepared_invoice['message']},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except stripe.error.InvalidRequestError as e:
        return Response(
            {'status': 'failed', 'error': str(e)},
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
            send_contact_email(serializer.validated_data)
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
        except Exception as e:
            logger.exception("Error processing contact form")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
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
