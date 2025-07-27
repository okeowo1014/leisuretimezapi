import uuid

def generate_booking_id():
    """ Generate a random 9-character booking ID (BKN + 6 Hex digits) """
    return 'BKN' + uuid.uuid4().hex[:6]

def generate_payment_id():
    """ Generate a random 9-character payment ID (PMT + 6 Hex digits) """
    return 'PMT' + uuid.uuid4().hex[:6]

def generate_transaction_id():
    """ Generate a random 19-character transaction ID (TXN + 16 Hex digits) """
    return 'TXN' + uuid.uuid4().hex[:16]

def reversedate(d):
    """ Convert date format from DD/MM/YYYY to YYYY-MM-DD """
    d = d.split('/')
    return '-'.join([d[2], d[1], d[0]])


from rest_framework import serializers
from .models import Booking, Contact

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from django.contrib.auth import logout
from .models import Booking, CustomerProfile, Contact
from .serializers import BookingSerializer, ContactSerializer
from .utils import generate_booking_id, reversedate

class CreatePersonalBookingAPIView(APIView):
    """ Create a personal booking """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        user = request.user

        try:
            profile = CustomerProfile.objects.get(user=user)
        except CustomerProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            daterange = data.get('daterange').split(' - ')
            travelcountry = data.get('travelcountry')

            booking = Booking.objects.create(
                customer=profile,
                booking_id=generate_booking_id(),
                package='personal',
                datefrom=reversedate(daterange[0]),
                dateto=reversedate(daterange[1]),
                purpose=data.get('purpose'),
                continent=data.get('continent'),
                travelcountry=travelcountry,
                travelstate=data.get('travelstate'),
                destinations='-'.join(data.getlist('destinations', [])),
                duration=int(data.get('duration', 0)),
                adult=int(data.get('adult', 0)),
                children=int(data.get('children', 0)),
                service='-'.join(data.getlist('service', [])),
                comment=data.get('comment', ''),
                lastname=data.get('lastname', ''),
                firstname=data.get('firstname', ''),
                profession=data.get('profession', ''),
                email=data.get('email', ''),
                phone=data.get('phone_full', ''),
                gender=data.get('gender', ''),
                country=data.get('country', ''),
                address=data.get('address', ''),
                city=data.get('city', ''),
                state=data.get('state', '')
            )

            serializer = BookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LogoutCustomerAPIView(APIView):
    """ Logout the authenticated customer """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)

class BookingSuccessAPIView(APIView):
    """ Display booking success page """
    def get(self, request):
        return Response({"message": "Booking successful"}, status=status.HTTP_200_OK)

class MessageSuccessAPIView(APIView):
    """ Display message success page """
    def get(self, request):
        return Response({"message": "Message sent successfully"}, status=status.HTTP_200_OK)

class SendContactMessageAPIView(APIView):
    """ Send a contact message """
    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Contact message sent successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SendMessageAPIView(APIView):
    """ Send a message related to a booking """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, bid):
        booking = get_object_or_404(Booking, booking_id=bid)
        # Handle message processing logic here
        return Response({"message": "Message sent successfully for booking " + bid}, status=status.HTTP_200_OK)



from django.urls import path
from .views import (
    CreatePersonalBookingAPIView, LogoutCustomerAPIView,
    BookingSuccessAPIView, MessageSuccessAPIView, SendContactMessageAPIView,
    SendMessageAPIView
)

urlpatterns = [
    path('create-personal-booking/', CreatePersonalBookingAPIView.as_view(), name='create-personal-booking'),
    path('logout/', LogoutCustomerAPIView.as_view(), name='logout'),
    path('booking-success/', BookingSuccessAPIView.as_view(), name='booking-success'),
    path('message-success/', MessageSuccessAPIView.as_view(), name='message-success'),
    path('send-contact-message/', SendContactMessageAPIView.as_view(), name='send-contact-message'),
    path('send-message/<str:bid>/', SendMessageAPIView.as_view(), name='send-message'),
]

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json
import stripe

from .models import (
    Package, CustomerProfile, Booking, Locations, Invoice, Payment
)
from .utils import (
    generate_booking_id, generate_transaction_id, generate_payment_id, get_country_info
)

def book_package(request, pid):
    package = Package.objects.get(package_id=pid)
    if request.method == 'POST':
        data = request.POST
        profile = CustomerProfile.objects.get(user=request.user)
        
        if data.get('update'):
            profile.address = data.get('address')
            profile.city = data.get('city')
            profile.state = data.get('state')
            profile.country = data.get('country')
            profile.phone = data.get('phone_full')
            profile.profession = data.get('profession')
            profile.save()
        
        booking = Booking(
            customer=profile,
            booking_id=generate_booking_id(),
            package=package.package_id,
            datefrom=package.date_from,
            dateto=package.date_to,
            purpose=package.name,
            continent=package.continent,
            travelcountry=package.country,
            travelstate=package.country,
            destinations=package.destinations,
            duration=package.duration,
            adult=int(data.get('noa')),
            children=int(data.get('noc')),
            service=package.services,
            comment=data.get('comment'),
            lastname=data.get('lastname'),
            firstname=data.get('firstname'),
            profession=data.get('profession'),
            email=data.get('email'),
            phone=data.get('phone_full'),
            gender=data.get('gender'),
            country=data.get('country'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state')
        )
        
        if package.price_option == 'fixed':
            booking.price = package.fixed_price
        else:
            offers = [
                {'adult': int(o[0]), 'children': int(o[1]), 'price': int(o[2])}
                for o in (i.split(',') for i in package.discount_price.split('-') if len(i) >= 3)
            ]
            offer = find_matching_offer(int(data.get('noa')), int(data.get('noc')), offers)
            if offer:
                booking.price = offer['price']
            else:
                messages.error(request, 'No matching offer found')
                return redirect(reverse('index:register-package', args=[pid]))
        
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f"{package.name} with {data.get('noa')} adult(s) and {data.get('noc')} child(ren)",
                            'images': [package.main_image.url]
                        },
                        'unit_amount': int(booking.price * 100),
                    },
                    'quantity': 1,
                },
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': f"{package.vat}% Tax"},
                        'unit_amount': int(package.vat * booking.price),
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            customer_email=request.user.email,
            success_url=f'https://www.leisuretimez.com/booking-complete/{booking.booking_id}',
            cancel_url='https://www.leisuretimez.com/cancelled',
        )
        
        booking.checkout_session_id = session.id
        booking.save()
        package.save()
        return redirect(session.url, code=303)
    
    return render(request, 'index/book-package.html', {'package': package})

@csrf_exempt
def search_countries_locations(request):
    if request.method == 'GET':
        country = request.GET.get('country')
        places = request.GET.get('places', '').split(',')
        country = get_country_info(country)[0]

        place_queries = Q()
        for place in places:
            place_queries |= Q(type__icontains=place)

        locations = Locations.objects.filter(Q(country__iexact=country) & place_queries)
        data = list(locations.values('title', 'state'))
        return JsonResponse({'locations': data}, status=200)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def preview_invoice(request, inv):
    invoice = Invoice.objects.get(invoice_id=inv)
    items = json.loads(invoice.items)
    return render(request, 'index/preview-invoice.html', {'invoice': invoice, 'items': items})

def find_matching_offer(adult, children, offers):
    for offer in offers:
        if offer['adult'] >= adult and offer['children'] >= children:
            return offer
    return None

def check_offer(request, pid):
    package = Package.objects.get(package_id=pid)
    if package.price_option == 'fixed':
        offers = [{'adult': package.max_adult_limit, 'children': package.max_child_limit, 'price': package.fixed_price}]
    else:
        offers = [
            {'adult': int(each[0]), 'children': int(each[1]), 'price': int(each[2])}
            for each in (i.split(',') for i in package.discount_price.split('-') if len(i) >= 3)
        ]
    
    adult = int(request.GET.get('adult', 0))
    children = int(request.GET.get('children', 0))
    matching_offer = find_matching_offer(adult, children, offers)
    
    return JsonResponse(matching_offer or {'error': 'No matching offer found'}, status=404)

def payment_success(request):
    return render(request, 'index/payment-success.html')

def get_invoice_number(value):
    return f'INV-{int(value.split("-")[1]) + 1:06}'

def create_package_invoice(booking, package):
    try:
        invoice_number = get_invoice_number(Invoice.objects.latest('invoice_id').invoice_id)
    except Invoice.DoesNotExist:
        invoice_number = 'INV-000001'

    subtotal = Decimal(booking.price)
    tax_amount = Decimal(package.vat) * subtotal / 100
    grandtotal = subtotal + tax_amount

    invoice = Invoice.objects.create(
        invoice_id=invoice_number,
        booking=booking,
        items=json.dumps([[package.name, 1, 'package', str(booking.price), str(subtotal)]]),
        subtotal=subtotal,
        tax=package.vat,
        tax_amount=tax_amount,
        total=grandtotal,
        admin_fee=0,
        admin_percentage=0,
    )
    
    booking.status = 'invoiced'
    booking.invoiced = True
    booking.invoice_id = invoice_number
    booking.save()
    package.applications += 1
    package.save()
    return invoice_number

def make_payment(request, inv):
    invoice = Invoice.objects.get(invoice_id=inv)
    txn = generate_transaction_id()
    
    Payment.objects.create(
        invoice=invoice,
        transaction_id=txn,
        payment_id=generate_payment_id(),
        amount=invoice.subtotal,
        vat=invoice.tax_amount,
        total=invoice.total,
        admin_fee=invoice.admin_fee,
    )
    
    invoice.status = 'paid'
    invoice.booking.status = 'paid'
    invoice.paid = True
    invoice.transaction_id = txn
    invoice.save()
    
    return redirect('index:payment-success')
