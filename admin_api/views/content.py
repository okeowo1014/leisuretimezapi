from django.db.models import Count
from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from admin_api.permissions import IsAdminStaff
from admin_api.serializers.content import (
    AdminBlogPostDetailSerializer, AdminBlogPostListSerializer,
    AdminBlogPostWriteSerializer, AdminCarouselSerializer,
    AdminDestinationDetailSerializer, AdminDestinationListSerializer,
    AdminDestinationWriteSerializer, AdminEventDetailSerializer,
    AdminEventListSerializer, AdminEventWriteSerializer,
    AdminPackageDetailSerializer, AdminPackageListSerializer,
    AdminPackageWriteSerializer, AdminPromoCodeSerializer,
)
from index.models import (
    BlogPost, Carousel, Destination, Event, Package, PromoCode,
)


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

class AdminPackageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminPackageWriteSerializer
        return AdminPackageListSerializer

    def get_queryset(self):
        qs = Package.objects.annotate(
            booking_count=Count('bookings'),
        ).order_by('-created_at')

        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=search) | Q(package_id__icontains=search))

        pkg_status = self.request.query_params.get('status')
        if pkg_status:
            qs = qs.filter(status=pkg_status)

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        return qs


class AdminPackageDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Package.objects.prefetch_related('package_images')

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return AdminPackageWriteSerializer
        return AdminPackageDetailSerializer


# ---------------------------------------------------------------------------
# Destinations
# ---------------------------------------------------------------------------

class AdminDestinationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminDestinationWriteSerializer
        return AdminDestinationListSerializer

    def get_queryset(self):
        qs = Destination.objects.order_by('-created_at')

        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=search) | Q(country__icontains=search))

        dest_status = self.request.query_params.get('status')
        if dest_status:
            qs = qs.filter(status=dest_status)

        return qs


class AdminDestinationDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Destination.objects.prefetch_related('destination_images')

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return AdminDestinationWriteSerializer
        return AdminDestinationDetailSerializer


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class AdminEventListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminEventWriteSerializer
        return AdminEventListSerializer

    def get_queryset(self):
        qs = Event.objects.order_by('-created_at')

        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=search) | Q(country__icontains=search))

        event_status = self.request.query_params.get('status')
        if event_status:
            qs = qs.filter(status=event_status)

        return qs


class AdminEventDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Event.objects.prefetch_related('event_images')

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return AdminEventWriteSerializer
        return AdminEventDetailSerializer


# ---------------------------------------------------------------------------
# Carousel
# ---------------------------------------------------------------------------

class AdminCarouselListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminCarouselSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Carousel.objects.order_by('position', '-created_at')


class AdminCarouselDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminCarouselSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Carousel.objects.all()


# ---------------------------------------------------------------------------
# Blog Posts
# ---------------------------------------------------------------------------

class AdminBlogPostListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminBlogPostWriteSerializer
        return AdminBlogPostListSerializer

    def get_queryset(self):
        qs = BlogPost.objects.select_related('author').annotate(
            comment_count=Count('comments', distinct=True),
            reaction_count=Count('reactions', distinct=True),
        ).order_by('-created_at')

        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(title__icontains=search) | Q(tags__icontains=search))

        blog_status = self.request.query_params.get('status')
        if blog_status:
            qs = qs.filter(status=blog_status)

        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class AdminBlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = BlogPost.objects.select_related('author')

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return AdminBlogPostWriteSerializer
        return AdminBlogPostDetailSerializer


# ---------------------------------------------------------------------------
# Promo Codes
# ---------------------------------------------------------------------------

class AdminPromoCodeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminPromoCodeSerializer

    def get_queryset(self):
        qs = PromoCode.objects.order_by('-created_at')

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(code__icontains=search)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        return qs


class AdminPromoCodeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminPromoCodeSerializer
    queryset = PromoCode.objects.all()
