from rest_framework import serializers
from .models import Package, Booking, Invoice, Payment, CustomerProfile

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = '__all__'


from rest_framework import serializers
from .models import Package, Booking, Invoice, Payment, CustomerProfile

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = '__all__'



from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PackageSerializer, BookingSerializer, InvoiceSerializer, PaymentSerializer, CustomerProfileSerializer
from .models import Package, Booking, Invoice, Payment, CustomerProfile

class BookPackageView(APIView):
    def post(self, request, pid):
        package = Package.objects.get(package_id=pid)
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.save(customer=request.user.customerprofile, package=package)
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
        locations = Locations.objects.filter(country__iexact=country, type__in=places)
        data = list(locations.values('title', 'state'))
        return Response({'locations': data}, status=status.HTTP_200_OK)

class PreviewInvoiceView(APIView):
    def get(self, request, inv):
        invoice = Invoice.objects.get(invoice_id=inv)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CheckOfferView(APIView):
    def get(self, request, pid):
        package = Package.objects.get(package_id=pid)
        adult = int(request.GET.get('adult', 0))
        children = int(request.GET.get('children', 0))
        offers = package.discount_price.split('-')
        offers = [offer.split(',') for offer in offers]
        offers = [{'adult': int(offer[0]), 'children': int(offer[1]), 'price': int(offer[2])} for offer in offers]
        matching_offer = next((offer for offer in offers if offer['adult'] >= adult and offer['children'] >= children), None)
        if matching_offer:
            return Response(matching_offer, status=status.HTTP_200_OK)
        return Response({'error': 'No matching offer found'}, status=status.HTTP_404_NOT_FOUND)

class MakePaymentView(APIView):
    def post(self, request, inv):
        invoice = Invoice.objects.get(invoice_id=inv)
        payment = Payment.objects.create(invoice=invoice)
        invoice.status = 'paid'
        invoice.save()
        return Response({'message': 'Payment successful'}, status=status.HTTP_200_OK)
    
from django.urls import path
from .views import BookPackageView, SearchCountriesLocationsView, PreviewInvoiceView, CheckOfferView, MakePaymentView

urlpatterns = [
    path('book-package/<str:pid>/', BookPackageView.as_view(), name='book-package'),
    path('search-locations/', SearchCountriesLocationsView.as_view(), name='search-locations'),
    path('preview-invoice/<str:inv>/', PreviewInvoiceView.as_view(), name='preview-invoice'),
    path('check-offer/<str:pid>/', CheckOfferView.as_view(), name='check-offer'),
    path('make-payment/<str:inv>/', MakePaymentView.as_view(), name='make-payment'),
]