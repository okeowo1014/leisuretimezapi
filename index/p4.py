from rest_framework import serializers
from .models import Package, Booking, CustomerProfile, Locations, Invoice, Payment

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = ('title', 'state')

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Package, Booking, CustomerProfile, Locations, Invoice, Payment
from .serializers import PackageSerializer, BookingSerializer, LocationSerializer, InvoiceSerializer, PaymentSerializer
import json

class BookPackageAPIView(APIView):
    def post(self, request, pid):
        try:
            package = Package.objects.get(package_id=pid)
            data = request.data
            profile = CustomerProfile.objects.get(user=request.user)
            update = data.get('update')

            if update:
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

            # Pricing logic based on options
            if package.price_option == 'fixed':
                booking.price = package.fixed_price
            else:
                g = [i.split(',') for i in package.discount_price.split('-') if len(i) >= 3]
                offers = [{'adult': int(each[0]), 'children': int(each[1]), 'price': int(each[2])} for each in g]
                offer = find_matching_offer(int(data.get('noa')), int(data.get('noc')), offers)
                if offer:
                    booking.price = offer['price']
                else:
                    return Response({'error': 'No matching offer found'}, status=status.HTTP_400_BAD_REQUEST)

            # Stripe session creation and saving booking
            session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f"{package.name} with {data.get('noa')} adult and {data.get('noc')} children",
                            'images': [f'{package.main_image.url}']},
                        'unit_amount': int(booking.price * 100),
                    },
                    'quantity': 1,
                }, {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f"{package.vat}% Tax",
                        },
                        'unit_amount': int(package.vat * booking.price),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                customer_email=request.user.email,
                success_url=f'https://www.leisuretimez.com/booking-complete/{booking.booking_id}',
                cancel_url='https://www.leisuretimez.com/cancelled',
            )

            booking.checkout_session_id = session.id
            booking.save()
            package.submissions += 1
            package.save()

            return Response({'checkout_url': session.url}, status=status.HTTP_201_CREATED)
        except Package.DoesNotExist:
            return Response({'error': 'Package not found'}, status=status.HTTP_404_NOT_FOUND)

class SearchCountriesLocationsAPIView(APIView):
    def get(self, request):
        country = request.GET.get('country')
        places = request.GET.get('places')
        places = places.split(',')
        country = get_country_info(country)[0]

        place_queries = Q()
        for place in places:
            place_queries |= Q(type__icontains=place)

        locations = Locations.objects.filter(Q(country__iexact=country) & place_queries)
        data = list(locations.values('title', 'state'))
        return Response({'locations': data}, status=status.HTTP_200_OK)

class PreviewInvoiceAPIView(APIView):
    def get(self, request, inv):
        try:
            invoice = Invoice.objects.get(invoice_id=inv)
            items = json.loads(invoice.items)
            return Response({'invoice': invoice, 'items': items}, status=status.HTTP_200_OK)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

class CheckOfferAPIView(APIView):
    def get(self, request, pid):
        package = Package.objects.get(package_id=pid)
        if package.price_option == 'fixed':
            offers = [{'adult': package.max_adult_limit, 'children': package.max_child_limit, 'price': package.fixed_price}]
        else:
            g = [i.split(',') for i in package.discount_price.split('-') if len(i) >= 3]
            offers = [{'adult': int(each[0]), 'children': int(each[1]), 'price': int(each[2])} for each in g]

        adult = int(request.GET.get('adult', 0))
        children = int(request.GET.get('children', 0))

        matching_offer = find_matching_offer(adult, children, offers)

        if matching_offer:
            return Response(matching_offer, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No matching offer found'}, status=status.HTTP_404_NOT_FOUND)


from django.urls import path
from .views import BookPackageAPIView, SearchCountriesLocationsAPIView, PreviewInvoiceAPIView, CheckOfferAPIView

urlpatterns = [
    path('api/book-package/<int:pid>/', BookPackageAPIView.as_view(), name='book-package-api'),
    path('api/search-locations/', SearchCountriesLocationsAPIView.as_view(), name='search-locations-api'),
    path('api/preview-invoice/<str:inv>/', PreviewInvoiceAPIView.as_view(), name='preview-invoice-api'),
    path('api/check-offer/<int:pid>/', CheckOfferAPIView.as_view(), name='check-offer-api'),
]
