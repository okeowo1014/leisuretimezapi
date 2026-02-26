from rest_framework import serializers

from index.models import (
    BlogPost, Carousel, Destination, DestinationImage, Event, EventImage,
    Package, PackageImage, PromoCode,
)


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

class AdminPackageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageImage
        fields = ('id', 'image')


class AdminPackageListSerializer(serializers.ModelSerializer):
    booking_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Package
        fields = (
            'id', 'package_id', 'name', 'category', 'price_option',
            'fixed_price', 'country', 'continent', 'duration',
            'availability', 'applications', 'submissions',
            'status', 'booking_count', 'created_at',
        )


class AdminPackageDetailSerializer(serializers.ModelSerializer):
    package_images = AdminPackageImageSerializer(many=True, read_only=True)

    class Meta:
        model = Package
        fields = '__all__'


class AdminPackageWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        exclude = ('bookings',)


# ---------------------------------------------------------------------------
# Destinations
# ---------------------------------------------------------------------------

class AdminDestinationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationImage
        fields = ('id', 'image')


class AdminDestinationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = (
            'id', 'name', 'country', 'continent', 'trips',
            'status', 'created_at',
        )


class AdminDestinationDetailSerializer(serializers.ModelSerializer):
    destination_images = AdminDestinationImageSerializer(many=True, read_only=True)

    class Meta:
        model = Destination
        fields = '__all__'


class AdminDestinationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = '__all__'


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class AdminEventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ('id', 'image')


class AdminEventListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            'id', 'name', 'country', 'continent', 'status', 'created_at',
        )


class AdminEventDetailSerializer(serializers.ModelSerializer):
    event_images = AdminEventImageSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = '__all__'


class AdminEventWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


# ---------------------------------------------------------------------------
# Carousel
# ---------------------------------------------------------------------------

class AdminCarouselSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carousel
        fields = '__all__'


# ---------------------------------------------------------------------------
# Blog
# ---------------------------------------------------------------------------

class AdminBlogPostListSerializer(serializers.ModelSerializer):
    author_email = serializers.CharField(source='author.email', read_only=True)
    comment_count = serializers.IntegerField(read_only=True, default=0)
    reaction_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = BlogPost
        fields = (
            'id', 'title', 'slug', 'author', 'author_email', 'status',
            'tags', 'comment_count', 'reaction_count',
            'published_at', 'created_at',
        )


class AdminBlogPostDetailSerializer(serializers.ModelSerializer):
    author_email = serializers.CharField(source='author.email', read_only=True)

    class Meta:
        model = BlogPost
        fields = '__all__'


class AdminBlogPostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = (
            'title', 'slug', 'content', 'excerpt', 'cover_image',
            'status', 'tags', 'published_at',
        )


# ---------------------------------------------------------------------------
# Promo Codes
# ---------------------------------------------------------------------------

class AdminPromoCodeSerializer(serializers.ModelSerializer):
    is_valid_now = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = '__all__'

    def get_is_valid_now(self, obj):
        return obj.is_valid()
