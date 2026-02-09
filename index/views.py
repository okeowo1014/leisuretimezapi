from decimal import Decimal
import json
import uuid
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from index.countrylist import get_country_info
from index.utils import send_invoice_email
from .models import Package, PackageImage, GuestImage, Destination, Event, CustomerProfile, Booking, Locations, Transaction, Wallet
from .serializers import CustomerProfileUpdateSerializer, PackageSerializer, PackageImageSerializer, GuestImageSerializer, DestinationSerializer, EventSerializer, CustomerProfileSerializer, BookingSerializer, LocationsSerializer, PackageSerializer, BookingSerializer, InvoiceSerializer, CustomerProfileSerializer
from rest_framework.views import APIView
from .models import Package, Booking, Invoice, Payment, CustomerProfile
# views.py
from rest_framework import viewsets, status,generics
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
import stripe
import requests
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from django.db.models import BooleanField, Exists, OuterRef
from django.db import models
# stripe.api_key = settings.STRIPE_SECRET_KEY
# API Views

# stripe.api_key = 'sk_test_51Q1AmzIdBWRin0jg8ra6JpGiXYhQj7JfcIJne6KzLOY0oHCwsNjkpqdRmHL9HhoaU0rvAKfKnDkKWwG2ulX698TF00BpR6ZCAn'
stripe.api_key = 'sk_test_51RJjB32KJEgBmA6Bs0Zhd2qh8ElLfOcg1bLi718romNjC54V4WTbr4eNhOKf3ySOK0AyjBECzUsFxpvsKsNvljY000b2rmr9JE'


def generate_booking_id():
    # generate randon 9 digit booking id with 3 letters prefix and 6 digits suffix
    prefix = 'BKN'
    suffix = uuid.uuid4().hex[:6]
    return prefix + suffix


def generate_payment_id():
    # generate randon 9 digit booking id with 3 letters prefix and 6 digits suffix
    prefix = 'PMT'
    suffix = uuid.uuid4().hex[:6]
    return prefix + suffix


def generate_transaction_id():
    # generate randon 9 digit booking id with 3 letters prefix and 6 digits suffix
    prefix = 'TXN'
    suffix = uuid.uuid4().hex[:16]
    return prefix + suffix


def reversedate(d):
    d = d.split('/')
    return '-'.join([d[2], d[1], d[0]])


@api_view(['GET'])
def index(request):
    # packages = Package.objects.filter(status='active')
    if request.user.is_authenticated:
        packages =  Package.objects.filter(
        status='active').order_by('-id', 'category').annotate(
            is_saved=Exists(request.user.saved_packages.filter(pk=OuterRef('pk'))))
    else:
        package= Package.objects.filter(status='active').order_by('-id', 'category').annotate(is_saved=models.Value(False, output_field=BooleanField()))

    destinations = Destination.objects.filter(status='active')
    events = Event.objects.filter(status='active')
    return Response({
        'packages': PackageSerializer(packages, many=True).data,
        'destinations': DestinationSerializer(destinations, many=True).data,
        'events': EventSerializer(events, many=True).data,
    })


@api_view(['GET'])
def package_list(request):
    if request.user.is_authenticated:
        packages =  Package.objects.filter(
        status='active').order_by('-id', 'category').annotate(
            is_saved=Exists(request.user.saved_packages.filter(pk=OuterRef('pk'))))
    else:
        package= Package.objects.filter(status='active').order_by('-id', 'category').annotate(is_saved=models.Value(False, output_field=BooleanField()))

    return Response(PackageSerializer(packages, many=True).data)


@api_view(['GET'])
def package_details(request, pid):
    package = get_object_or_404(Package, package_id=pid)
    package_images = PackageImage.objects.filter(package=package)
    guest_images = GuestImage.objects.filter(package=package)
    return Response({
        'package': PackageSerializer(package).data,
        'package_images': PackageImageSerializer(package_images, many=True).data,
        'guest_images': GuestImageSerializer(guest_images, many=True).data,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def personal_booking(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)
    return Response(CustomerProfileSerializer(profile).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def booking_history(request):
    history = Booking.objects.filter(customer__user=request.user)
    return Response(BookingSerializer(history, many=True).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def account_settings(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)
    history = Booking.objects.filter(customer__user=request.user)
    return Response({
        'profile': CustomerProfileSerializer(profile).data,
        'booking_histories': BookingSerializer(history, many=True).data
    })


@api_view(['GET'])
def search_locations(request):
    print(request.GET)
    country = request.GET.get('country')
    states = request.GET.getlist('state')
    location_type = request.GET.get('type')
    print(country, states, location_type)

    state_queries = Q()
    for state in states:
        state_queries |= Q(state__icontains=state)

    locations = Locations.objects.filter(
        Q(country__iexact=country) & state_queries & Q(
            type__iexact=location_type)
    )
    # locations = Locations.objects.filter(
    #     Q(country__iexact=country) & state_queries)

    # locations=Locations.objects.all()
    print(locations.values('title', 'type', 'city', 'state', 'country')[:5])
    return Response(LocationsSerializer(locations, many=True).data)



@permission_classes([IsAuthenticated])
class PreviewInvoiceView(APIView):
    def get(self, request, inv):
        invoice = get_object_or_404(Invoice, invoice_id=inv)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


def get_price(pid,adult=0,children=0):
    package = Package.objects.get(package_id=pid)
    if package.price_option == 'fixed':
        return package.fixed_price
    else:
        offers = package.discount_price.split('-')
        offers = [offer.split(',') for offer in offers if len(offer) >= 3]
        offers = [{'adult': int(offer[0]), 'children': int(
            offer[1]), 'price': int(offer[2])} for offer in offers]
        matching_offer = next(
            (offer for offer in offers if offer['adult'] >= adult and offer['children'] >= children), None)
        return matching_offer['price'] or 0



@permission_classes([IsAuthenticated])
class BookPackageView(APIView):
    def post(self, request, pid):
        package = Package.objects.get(package_id=pid)
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.save(
                customer=request.user.customerprofile, package=package, booking_id=generate_booking_id())
            # Create invoice and payment
            invoice = Invoice.objects.create(booking=booking, package=package)
            payment = Payment.objects.create(invoice=invoice)
            return Response({'message': 'Booking successful'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SearchCountriesLocationsView(APIView):
    def get(self, request):
        country = request.GET.get('country')
        places = request.GET.get('places')
        places = places.split(',')
        country = get_country_info(country)[0]
        locations = Locations.objects.filter(
            country__iexact=country, type__in=places)
        data = list(locations.values('title', 'state'))
        return Response({'locations': data}, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class PreviewInvoiceView(APIView):
    def get(self, request, inv):
        invoice = get_object_or_404(Invoice, invoice_id=inv)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class CheckOfferView(APIView):
    def get(self, request, pid):
        package = Package.objects.get(package_id=pid)
        adult = int(request.GET.get('adult', 0))
        children = int(request.GET.get('children', 0))
        offers = package.discount_price.split('-')
        print(offers)
        offers = [offer.split(',') for offer in offers if len(offer) >= 3]
        print(offers)
        offers = [{'adult': int(offer[0]), 'children': int(
            offer[1]), 'price': int(offer[2])} for offer in offers]
        matching_offer = next(
            (offer for offer in offers if offer['adult'] >= adult and offer['children'] >= children), None)
        if matching_offer:
            return Response(matching_offer, status=status.HTTP_200_OK)
        return Response({'error': 'No matching offer found'}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class MakePaymentView(APIView):
    def post(self, request, inv):
        invoice = get_object_or_404(Invoice, invoice_id=inv)
        payment = Payment.objects.create(invoice=invoice)
        invoice.status = 'paid'
        invoice.save()
        return Response({'message': 'Payment successful'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_display_picture(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)
    if 'file' in request.FILES:
        profile.image = request.FILES['file']
        profile.save()
        return Response({'image_url': profile.image.url}, status=status.HTTP_200_OK)
    return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)


def get_invoice_number(value):
    return 'INV-'+str(int(value.split('-')[1])+1).zfill(6)



def create_package_invoice(booking,package):
    # booking=Booking.objects.get(booking_id=bid)
    try:
        # print('getting invoice number')
        invoice_number=get_invoice_number(Invoice.objects.latest('invoice_id').invoice_id)
    except:
        # print('setting invoice number')
        invoice_number='INV-000001'
    # print(invoice_number)
    tax=package.vat
    notes=booking.comment
    names=[package.name]
    quantity=[1]
    units=['package']
    prices=[booking.price]
    unitprice=[Decimal(qty)*Decimal(prc) for qty,prc in zip(quantity,prices)]
    items=json.dumps([[name,quantity,unit,str(price),str(unitprc)] for name,quantity,unit,price,unitprc in zip(names,quantity,units,prices,unitprice)])
    subtotal=sum([Decimal(quantity) * Decimal(price) for name,quantity,unit,price in zip(names,quantity,units,prices)])
    # tax_amount=Decimal(tax) * subtotal / 100
    # grandtotal=subtotal+tax_amount
    service_charge_percent=0
    sc_amount=Decimal(service_charge_percent) * subtotal / 100
    tax_amount=Decimal(tax) * (subtotal+sc_amount) / 100
    grandtotal=subtotal+tax_amount+sc_amount
    try:
        booking.invoice_id
        Invoice.objects.create(
            invoice_id=invoice_number,
            booking=booking,
            items=items,
            subtotal=subtotal,
            tax=tax,
            tax_amount=tax_amount,
            total=grandtotal,
            admin_fee=sc_amount,
            admin_percentage=service_charge_percent
        )
        booking.status='invoiced'
        booking.invoiced=True
        booking.invoice_id=invoice_number
        booking.save()
        package.applications+=1
        package.save()
        return invoice_number
    except:
        return None


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
    lookup_field = 'booking_id' 

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(customer__user=self.request.user)

    def perform_create(self, serializer):
        customer = CustomerProfile.objects.get(user=self.request.user)
        print(serializer.validated_data)
        price=get_price(serializer.validated_data['package'],serializer.validated_data['adult'],serializer.validated_data['children'])
        # print('price is ',price)
        serializer.save(customer=customer,booking_id=generate_booking_id(),price=price)


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
        booking = get_object_or_404(
            Booking, booking_id=request.data.get('booking_id'))

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
            success_url=request.build_absolute_uri(
                f'/api/bookings/complete/{booking.booking_id}/'),
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
                invoice_url = request.build_absolute_uri(
                    f'/print-invoice/{invoice.invoice_id}/')
                pdf_path = publish_invoice(invoice_url, booking.booking_id)

                # Send email
                customer_name = f'{booking.firstname} {booking.lastname}'
                send_invoice_email(booking.email, customer_name,
                                   invoice.invoice_id, pdf_path)

                return Response({'status': 'success', 'message': 'Payment processed successfully'})

            return Response({'error': 'Failed to create invoice'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Payment not completed'},
                        status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET'])
# def publish_invoice(request, invoice_id):
#     try:
#         invoice = get_object_or_404(Invoice, invoice_id=invoice_id)
#         response = requests.post(
#             'https://api.pdfshift.io/v3/convert/pdf',
#             auth=('api', settings.PDFSHIFT_API_KEY),
#             json={
#                 "source": request.build_absolute_uri(f'/print-invoice/{invoice_id}/'),
#                 "landscape": False,
#                 "use_print": False
#             }
#         )
#         response.raise_for_status()

#         return Response({'pdf_url': response.url})
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def publish_invoice(url,p_n):
    response = requests.post(
        'https://api.pdfshift.io/v3/convert/pdf',
        auth=('api', 'sk_53a33801e417788102727e7831d1c50b56446982'),
        json={
            "source": url,
            "landscape": False,
            "use_print": False
        }
    )
    response.raise_for_status()
    file_name = f"/home/findepbl/leisuretimezmedia/customer/invoices/{p_n}.pdf".replace(' ', '_')

    with open(file_name, 'wb') as f:
        f.write(response.content)
    f.close()
    return file_name


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
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'status': 'error',
        'message': 'Invalid data provided',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)




class CustomerProfileDetailView(generics.RetrieveUpdateAPIView):
    # serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser,JSONParser)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH', 'POST']:
            return CustomerProfileUpdateSerializer
        return CustomerProfileSerializer

    def get_object(self):
        """
        Get the profile for the current user
        """
        return get_object_or_404(CustomerProfile, user=self.request.user)

    def post(self, request, *args, **kwargs):
        """
        Handle partial updates
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        Handle full updates
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerProfileImageUpdateView(generics.UpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        return get_object_or_404(CustomerProfile, user=self.request.user)

    def post(self, request, *args, **kwargs):
        """
        Handle profile image updates
        """
        profile = self.get_object()
        
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile.image = request.FILES['image']
        profile.save()

        serializer = self.get_serializer(profile)
        return Response(serializer.data)


# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from .models import Package

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_package(request, package_id):
    try:
        package = Package.objects.get(package_id=package_id)
    except Package.DoesNotExist:
        return Response({'error': 'Package not found'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if package in user.saved_packages.all():
        return Response({'message': f'Package "{package.name}" is already saved'}, status=status.HTTP_208_ALREADY_REPORTED)
    else:
        user.saved_packages.add(package)
        return Response({'message': f'Package "{package.name}" saved successfully'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unsave_package(request, package_id):
    try:
        package = Package.objects.get(package_id=package_id)
    except Package.DoesNotExist:
        return Response({'error': 'Package not found'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    user.saved_packages.remove(package)
    return Response({'message': f'Package "{package.name}" unsaved successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_saved_packages(request):
    user = request.user
    saved_packages = user.saved_packages.all()
    serializer = PackageSerializer(saved_packages, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



def pay_invoice(inv):
    invoice=Invoice.objects.get(invoice_id=inv)
    # print(invoice,invoice.subtotal,invoice.tax_amount,invoice.total)
    txn=generate_transaction_id()
    Payment.objects.create(
        invoice=invoice,
        transaction_id=txn,
        payment_id=generate_payment_id(),
        amount=Decimal(invoice.subtotal),
        vat=Decimal(invoice.tax_amount),
        total=Decimal(invoice.total),
        admin_fee=Decimal(invoice.admin_fee),
    )
    invoice.status='paid'
    invoice.booking.status='paid'
    invoice.paid=True
    invoice.transaction_id=txn
    invoice.save()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pay_booking(request,booking_id,mode='wallet'):
    try:
        booking=get_object_or_404(Booking, booking_id=booking_id,customer__user=request.user)
        if booking.status == 'paid':
            return Response({'status':'failed','message':'already paid'},status=status.HTTP_400_BAD_REQUEST)
        elif booking.status == 'pending':
            package=Package.objects.get(package_id=booking.package)
            if mode=='wallet':
                wallet=Wallet.objects.get(user=request.user)
                withdraw=wallet.withdraw(booking.price)
                if withdraw:
                    withdraw.description=f'payment for booking'
                    withdraw.reference=booking.booking_id
                    withdraw.save()
                    print(withdraw)
                    booking.status='paid'
                    booking.payment_status=True
                    booking.checkout_session_id='wallet'
                    booking.save()
                    return Response({
                    'status':'successful',
                    'booking_id':booking.booking_id,
                    'mode': 'wallet'
                    })
                else:
                    return Response({
                    'status':'failed',
                    'message':'insufficient balance'
                    },status=status.HTTP_400_BAD_REQUEST)
                # invoice=create_package_invoice(booking,package)
                # if invoice:
                #     pay_invoice(invoice)
                #     # pay_invoice(booking.invoice_id)
                #     package.submissions+=1
                #     package.bookings.add(booking)
                #     package.save()
                #     fn=publish_invoice(f'https://www.leisuretimez.com/print-invoice/{invoice}/',booking.booking_id)
                #     customer_name=f'{booking.customer.user.lastname} {booking.customer.user.firstname}'
                #     send_invoice_email(booking.customer.user.email,customer_name, invoice, fn)
            else:
                session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                    'currency': 'usd',
                    'product_data': {
                    'name': f"{package.name} with {booking.adult} adult and {booking.children} children",
                    'images': [f'{package.main_image.url}']},
                    'unit_amount': int(booking.price* 100),
                    },
                    'quantity': 1,
                    },{
                            'price_data': {
                                'currency': 'usd',
                                'product_data': {
                                    'name': f"{package.vat}% Tax",
                                },
                                'unit_amount': int(package.vat *  booking.price),
                            },
                            'quantity': 1,
                        }],
                mode='payment',
                customer_email=request.user.email,#customer_email='okeowo1014@gmail.com'
                success_url=f'https://api.leisuretimez.com/payment/success',
                cancel_url='https://api.leisuretimez.com/payment/cancel',
                metadata= {'booking_id':booking.booking_id, 'type': 'booking_payment'},
                )
                booking.checkout_session_id=session.id
                booking.save()
                return Response({
                    'status':'successful',
                    'checkout_url':session.url,
                    'session_id': session.id,
                    'mode': 'checkout'
        
                    })
        else:
            return Response({
                'status':'failed',
                'message':f'booking status is {booking.status}'
            },status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
                'status':'failed',
                'message':str(e)
            },status=status.HTTP_400_BAD_REQUEST)
    

def prepare_invoice(booking,package):
    try:
        invoice=create_package_invoice(booking,package)
        if invoice:
            pay_invoice(invoice)
            # pay_invoice(booking.invoice_id)
            package.submissions+=1
            package.bookings.add(booking)
            package.save()
            fn=publish_invoice(f'https://www.leisuretimez.com/print-invoice/{invoice}/',booking.booking_id)
            customer_name=f'{booking.customer.user.lastname} {booking.customer.user.firstname}'
            send_invoice_email(booking.customer.user.email,customer_name, invoice, fn)
            return  {'status':'successful','message':'invoice created'}
            # return Response({
            # 'status':'successful',
            # 'booking_id':booking.booking_id,
            # # 'session_id': session.id,
            # })
    except Exception as e:
        return{'status':'failed','message':str(e)}
        # return Response({
        #         'status':'failed',
        #         'message':str(e)
        #     },status=status.HTTP_400_BAD_REQUEST)




# @api_view(['POST']) 
# @permission_classes([IsAuthenticated])
# def confirm_booking(request):
#     booking_id = request.POST.get('booking_id', None)
#     if not booking_id:
#         session_id = request.POST.get('session_id', None)
#         if not session_id:
#             return Response({'error': 'Booking ID or Session ID not provided.'}, status=400)
#     if booking_id:
#         booking=get_object_or_404(Booking, booking_id=booking_id,customer__user=request.user,checkout_session_id__isnull=False)
#         trans=Transaction.objects.get(reference=booking.booking_id,transaction_type='Withdrawal',status='Completed')
#         if not trans:
#             return Response({'error':'Transaction not found'},status=status.HTTP_400_BAD_REQUEST)
#     else:
#         try:
#             session = stripe.checkout.Session.retrieve(session_id)
#             payment_status = session.get('payment_status')
#             customer_email = session.get('customer_email')

#             if payment_status == 'paid':
#                 try:
#                     booking=get_object_or_404(Booking,customer__user=request.user,checkout_session_id=session_id)
#                     package=Package.objects.get(package_id=booking.package)
#                 except Booking.DoesNotExist:
#                     return Response({'status':'failed','error': 'Booking not found.'}, status=400)
#                 except Package.DoesNotExist:
#                     return Response({'status':'failed','error': 'Package not found.'}, status=400)
#             else:
#                 return Response({'status':'failed','error': 'Paument Not Found'})
#         except stripe.error.InvalidRequestError as e:
#             return Response({'status':'failed','error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

#     # booking=get_object_or_404(Booking, customer__user=request.user,checkout_session_id=session_id)
#     # package=Package.objects.get(package_id=booking.package)
#     if package.bookings.filter(id=booking.id).exists():
#         return Response({'error':'You have booked this package already'},status=status.HTTP_400_BAD_REQUEST)
#     # if booking.checkout_session_id == 'wallet':
#     #     print(booking.booking_id)
#     #     print(Transaction.objects.get(reference=booking.booking_id))

#     # else:
#     #     session=stripe.checkout.Session.retrieve(booking.checkout_session_id)
#     #     if session.payment_status == "paid":
#     booking.payment_status=True
#     booking.save()
#     prepared_invoice=prepare_invoice(booking,package)
#     if prepared_invoice['status'] == 'successful':
#         booking.status='paid'
#         booking.payment_status=True
#         booking.save()
#         return Response({'status':'successful','booking_id':booking.booking_id,'mode': booking.checkout_session_id})
#     else:
#         return Response({'status':'failed','error': prepared_invoice['message']}, status=400)
  
#         #     booking.status='paid'
#         #     booking.payment_status=True
#         #     booking.save()
#         #     invoice=create_package_invoice(booking,package)
#         # if invoice:
#         #     pay_invoice(invoice)
#         #     # pay_invoice(booking.invoice_id)
#         #     package.submissions+=1
#         #     package.bookings.add(booking)
#         #     package.save()
#         #     fn=publish_invoice(f'https://www.leisuretimez.com/print-invoice/{invoice}/',booking.booking_id)
#         #     customer_name=f'{booking.customer.user.lastname} {booking.customer.user.firstname}'
#         #     send_invoice_email(booking.customer.user.email,customer_name, invoice, fn)
#         #     return Response({
#         #     'booking_id':booking.booking_id,
#         #     'session_id': session.id,
#         #     'mode': 'checkout'
#         #     })


# @api_view(['POST']) 
# @permission_classes([IsAuthenticated])
# def confirm_booking(request):
#     booking_id = request.POST.get('booking_id', None)
#     if not booking_id:
#         session_id = request.POST.get('session_id', None)
#         if not session_id:
#             return Response({'error': 'Booking ID or Session ID not provided.'}, status=400)
#     if booking_id:
#         booking=get_object_or_404(Booking, booking_id=booking_id,customer__user=request.user,checkout_session_id__isnull=False)
#         trans=Transaction.objects.get(reference=booking.booking_id,transaction_type='Withdrawal',status='Completed')
#         if not trans:
#             return Response({'error':'Transaction not found'},status=status.HTTP_400_BAD_REQUEST)
#     else:
#         try:
#             session = stripe.checkout.Session.retrieve(session_id)
#             payment_status = session.get('payment_status')
#             customer_email = session.get('customer_email')

#             if payment_status == 'paid':
#                 try:
#                     booking=get_object_or_404(Booking,customer__user=request.user,checkout_session_id=session_id)
#                     package=Package.objects.get(package_id=booking.package)
#                 except Booking.DoesNotExist:
#                     return Response({'status':'failed','error': 'Booking not found.'}, status=400)
#                 except Package.DoesNotExist:
#                     return Response({'status':'failed','error': 'Package not found.'}, status=400)
#             else:
#                 return Response({'status':'failed','error': 'Paument Not Found'})
#         except stripe.error.InvalidRequestError as e:
#             return Response({'status':'failed','error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#     if package.bookings.filter(id=booking.id).exists():
#         return Response({'error':'You have booked this package already'},status=status.HTTP_400_BAD_REQUEST)

#     booking.payment_status=True
#     booking.save()
#     prepared_invoice=prepare_invoice(booking,package)
#     if prepared_invoice['status'] == 'successful':
#         booking.status='paid'
#         booking.payment_status=True
#         booking.save()
#         return Response({'status':'successful','booking_id':booking.booking_id,'mode': booking.checkout_session_id})
#     else:
#         return Response({'status':'failed','error': prepared_invoice['message']}, status=400)
  

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_booking(request):
    identifier = request.data.get('identifier')
    mode = request.data.get('mode')

    if not identifier and not mode:
        return Response({'error': 'Booking ID or Session ID not provided.'}, status=status.HTTP_400_BAD_REQUEST)

    booking = None
    package = None

    if mode == 'wallet':
        booking = get_object_or_404(
            Booking,
            booking_id=identifier.strip(),
            customer__user=request.user,
            checkout_session_id__isnull=False
        )

        try:
            trans = Transaction.objects.get(
                reference=booking.booking_id,
                transaction_type='Withdrawal',
                status='Completed'
            )
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_400_BAD_REQUEST)

    else:
        try:
            identifier = identifier.strip()
            session = stripe.checkout.Session.retrieve(identifier)
            if session.get('payment_status') != 'paid':
                return Response({'status': 'failed', 'error': 'Payment not found'}, status=status.HTTP_400_BAD_REQUEST)

            booking = get_object_or_404(
                Booking,
                customer__user=request.user,
                checkout_session_id=identifier
            )

        except stripe.error.InvalidRequestError as e:
            return Response({'status': 'failed', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Booking.DoesNotExist:
            return Response({'status': 'failed', 'error': 'Booking not found'}, status=status.HTTP_400_BAD_REQUEST)
        except Package.DoesNotExist:
            return Response({'status': 'failed', 'error': 'Package not found'}, status=status.HTTP_400_BAD_REQUEST)
        
    package = get_object_or_404(Package, package_id=booking.package)
    # Ensure the user hasn't already booked this package
    if package.bookings.filter(id=booking.id).exists() and booking.status == 'paid':
        return Response({'error': 'You have already booked this package.'}, status=status.HTTP_409_CONFLICT)

    # Update booking payment status
    booking.payment_status = True
    booking.save()

    # Prepare invoice
    prepared_invoice = prepare_invoice(booking, package or booking.package)
    if prepared_invoice.get('status') == 'successful':
        booking.status = 'paid'
        booking.save()
        return Response({
            'status': 'successful',
            'booking_id': booking.booking_id,
            'mode': booking.checkout_session_id
        })

    return Response({
        'status': 'failed',
        'error': prepared_invoice.get('message', 'Invoice preparation failed.')
    }, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_booking_payment(request):
    session_id = request.POST.get('session_id')
    if not session_id:
        return Response({'error': 'Session ID not provided.'}, status=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.get('payment_status')
        customer_email = session.get('customer_email')

        if payment_status == 'paid':
            try:
                booking=get_object_or_404(Booking,customer__user=request.user,checkout_session_id=session_id)
                package=Package.objects.get(package_id=booking.package)
            except Booking.DoesNotExist:
                return Response({'status':'failed','error': 'Booking not found.'}, status=400)
            except Package.DoesNotExist:
                return Response({'status':'failed','error': 'Package not found.'}, status=400)
            prepared_invoice=prepare_invoice(booking,package)
            if prepared_invoice['status'] == 'successful':
                booking.status='paid'
                booking.payment_status=True
                booking.save()
                return Response({'status':'successful','booking_id':booking.booking_id,'mode': booking.checkout_session_id})
            else:
                return Response({'status':'failed','error': prepared_invoice['message']}, status=400)
        else:
            return Response({'status':'failed','error': 'Paument Not Found'})
    except stripe.error.InvalidRequestError as e:
        return Response({'status':'failed','error': str(e)}, status=status.HTTP_400_BAD_REQUEST)






# urls.py



# def get_packages_with_save_status(user, queryset):
#     """
#     Annotates a Package queryset with a 'is_saved' boolean field
#     indicating if the given user has saved each package.
#     """
#     if user.is_authenticated:
#         return queryset.annotate(
#             is_saved=Exists(user.saved_packages.filter(pk=OuterRef('pk')))
#         )
#     else:
#         return queryset.annotate(is_saved=models.Value(False, output_field=BooleanField()))

# # In your view or wherever you fetch packages:
# from .models import Package
# from .utils import get_packages_with_save_status # Assuming the function is in utils.py

# def package_list_view(request):
#     all_packages = Package.objects.all()
#     packages_with_save_status = get_packages_with_save_status(request.user, all_packages)
#     # Serialize 'packages_with_save_status' and return in your API response
#     # ...

class CruiseBookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'booking_id' 

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(customer__user=self.request.user)

    def perform_create(self, serializer):
        customer = CustomerProfile.objects.get(user=self.request.user)
        print(serializer.validated_data)
        # price=get_price(serializer.validated_data['package'],serializer.validated_data['adult'],serializer.validated_data['children'])
        # print('price is ',price)
        serializer.save(customer=customer,booking_id=generate_booking_id())