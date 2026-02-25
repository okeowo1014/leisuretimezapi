from django.contrib import admin

from .models import (
    AccountDeletionLog, AdminProfile, BlogComment, BlogPost, BlogReaction,
    Booking, BookingActivityLog, BookingService, Carousel, Contact,
    CruiseType, CustomUser, CustomerProfile, Destination, DestinationImage,
    Event, EventImage, EventType, GuestImage, Invoice, Locations,
    Notification, Package, PackageImage, Payment, PaymentSchedule,
    PersonalisedBooking, PersonalisedBookingAttachment,
    PersonalisedBookingInvoice, PersonalisedBookingMessage,
    PersonalisedBookingPayment, ProcessedStripeEvent, PromoCode, Quotation,
    QuotationLineItem, Review, ServiceCatalog, SupportMessage,
    SupportTicket, Transaction, Wallet,
)


# ---------------------------------------------------------------------------
# Inline admins
# ---------------------------------------------------------------------------

class PackageImageInline(admin.TabularInline):
    model = PackageImage
    extra = 1


class GuestImageInline(admin.TabularInline):
    model = GuestImage
    extra = 1


class DestinationImageInline(admin.TabularInline):
    model = DestinationImage
    extra = 1


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1


class BookingServiceInline(admin.TabularInline):
    model = BookingService
    extra = 0
    raw_id_fields = ['service']


class PersonalisedBookingMessageInline(admin.TabularInline):
    model = PersonalisedBookingMessage
    extra = 0
    readonly_fields = ['sender', 'created_at']


class PersonalisedBookingAttachmentInline(admin.TabularInline):
    model = PersonalisedBookingAttachment
    extra = 0
    readonly_fields = ['uploaded_by', 'created_at']


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ['sender', 'created_at']


class QuotationLineItemInline(admin.TabularInline):
    model = QuotationLineItem
    extra = 1


class PersonalisedBookingPaymentInline(admin.TabularInline):
    model = PersonalisedBookingPayment
    extra = 0
    readonly_fields = ['payment_id', 'status', 'completed_at', 'created_at']


class PaymentScheduleInline(admin.TabularInline):
    model = PaymentSchedule
    extra = 0


class BookingActivityLogInline(admin.TabularInline):
    model = BookingActivityLog
    extra = 0
    readonly_fields = ['action', 'actor', 'description', 'old_value', 'new_value', 'created_at']
    ordering = ['-created_at']


# ---------------------------------------------------------------------------
# User & Profiles
# ---------------------------------------------------------------------------

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'firstname', 'lastname', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'status']
    search_fields = ['email', 'firstname', 'lastname']
    ordering = ['-date_joined']


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'country', 'city', 'status']
    search_fields = ['user__email', 'phone']
    list_filter = ['status', 'country']


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'designation', 'status']


# ---------------------------------------------------------------------------
# Dynamic Lookup Tables
# ---------------------------------------------------------------------------

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'position']
    list_editable = ['is_active', 'position']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['position', 'name']


@admin.register(CruiseType)
class CruiseTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'position']
    list_editable = ['is_active', 'position']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['position', 'name']


@admin.register(ServiceCatalog)
class ServiceCatalogAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'base_price', 'is_active', 'position']
    list_editable = ['is_active', 'position', 'base_price']
    list_filter = ['category', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['position', 'name']


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'country', 'continent', 'fixed_price', 'status', 'created_at']
    list_filter = ['status', 'category', 'continent']
    search_fields = ['name', 'package_id']
    inlines = [PackageImageInline, GuestImageInline]


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id', 'customer', 'package', 'price', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method']
    search_fields = ['booking_id', 'email', 'firstname', 'lastname']
    ordering = ['-created_at']


@admin.register(PersonalisedBooking)
class PersonalisedBookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'event_type', 'cruise_type', 'status',
        'date_from', 'date_to', 'quote_amount', 'assigned_to', 'created_at',
    ]
    list_filter = ['status', 'event_type', 'cruise_type', 'requires_accommodation']
    search_fields = ['user__email', 'event_name', 'preferred_destination']
    raw_id_fields = ['user', 'assigned_to']
    inlines = [
        BookingServiceInline, PersonalisedBookingMessageInline,
        PersonalisedBookingAttachmentInline, PaymentScheduleInline,
        BookingActivityLogInline,
    ]
    fieldsets = (
        ('Core', {
            'fields': ('user', 'event_type', 'event_name', 'status'),
        }),
        ('Dates & Duration', {
            'fields': ('date_from', 'date_to', 'duration_hours', 'duration_days'),
        }),
        ('Cruise', {
            'fields': ('cruise_type',),
        }),
        ('Location', {
            'fields': ('continent', 'country', 'state', 'preferred_destination'),
        }),
        ('Guests', {
            'fields': ('guests', 'adults', 'children'),
        }),
        ('Legacy Services', {
            'fields': ('catering', 'bar_attendance', 'decoration', 'special_security', 'photography', 'entertainment'),
            'classes': ('collapse',),
        }),
        ('Budget & Pricing', {
            'fields': ('budget_min', 'budget_max', 'quote_amount', 'quote_expires_at', 'deposit_amount', 'deposit_paid'),
        }),
        ('Accommodation', {
            'fields': ('requires_accommodation', 'accommodation_type'),
        }),
        ('Notes & Comments', {
            'fields': ('additional_comments', 'special_requests', 'admin_notes', 'rejection_reason', 'cancellation_reason'),
        }),
        ('Admin', {
            'fields': ('assigned_to', 'terms_accepted'),
        }),
    )


# ---------------------------------------------------------------------------
# Invoices & Payments
# ---------------------------------------------------------------------------

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_id', 'booking', 'total', 'paid', 'status', 'created_at']
    list_filter = ['status', 'paid']
    search_fields = ['invoice_id']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'invoice', 'total', 'paid', 'status', 'created_at']
    list_filter = ['status', 'paid']


# ---------------------------------------------------------------------------
# Quotations & Personalised Booking Invoices/Payments
# ---------------------------------------------------------------------------

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'version', 'status', 'subtotal', 'total', 'created_by', 'created_at']
    list_filter = ['status']
    search_fields = ['booking__user__email', 'booking__event_name']
    raw_id_fields = ['booking', 'created_by']
    readonly_fields = ['subtotal', 'tax_amount', 'total', 'accepted_at', 'rejected_at']
    inlines = [QuotationLineItemInline]


@admin.register(PersonalisedBookingInvoice)
class PersonalisedBookingInvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'booking', 'quotation', 'status', 'total', 'amount_paid', 'balance_due', 'due_date']
    list_filter = ['status']
    search_fields = ['invoice_number', 'booking__user__email']
    raw_id_fields = ['booking', 'quotation', 'created_by']
    readonly_fields = ['invoice_number', 'balance_due']
    inlines = [PersonalisedBookingPaymentInline]

    def balance_due(self, obj):
        return obj.balance_due
    balance_due.short_description = 'Balance Due'


@admin.register(PersonalisedBookingPayment)
class PersonalisedBookingPaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'invoice', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['payment_method', 'status']
    search_fields = ['payment_id', 'stripe_payment_intent_id', 'invoice__invoice_number']
    readonly_fields = ['payment_id', 'completed_at']


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'milestone_name', 'amount', 'due_date', 'status']
    list_filter = ['status']
    search_fields = ['booking__user__email', 'milestone_name']
    raw_id_fields = ['booking', 'invoice']


@admin.register(BookingActivityLog)
class BookingActivityLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'action', 'actor', 'created_at']
    list_filter = ['action']
    search_fields = ['booking__user__email', 'description']
    raw_id_fields = ['booking', 'actor']
    readonly_fields = ['booking', 'action', 'actor', 'description', 'old_value', 'new_value', 'metadata', 'created_at']


# ---------------------------------------------------------------------------
# Destinations & Events
# ---------------------------------------------------------------------------

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'continent', 'trips', 'status']
    list_filter = ['status', 'continent']
    search_fields = ['name', 'country']
    inlines = [DestinationImageInline]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'continent', 'status']
    list_filter = ['status']
    search_fields = ['name']
    inlines = [EventImageInline]


# ---------------------------------------------------------------------------
# Wallet & Transactions
# ---------------------------------------------------------------------------

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'is_active', 'created_at']
    search_fields = ['user__email']
    list_filter = ['is_active']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'wallet', 'transaction_type', 'amount', 'status', 'created_at']
    list_filter = ['transaction_type', 'status']
    search_fields = ['wallet__user__email', 'reference']


# ---------------------------------------------------------------------------
# Reviews & Promo Codes
# ---------------------------------------------------------------------------

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'rating', 'created_at']
    list_filter = ['rating']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'is_active', 'current_uses', 'max_uses', 'valid_to']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code']


# ---------------------------------------------------------------------------
# Notifications & Support
# ---------------------------------------------------------------------------

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['user__email', 'title']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'subject', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['user__email', 'subject']
    inlines = [SupportMessageInline]


# ---------------------------------------------------------------------------
# Blog
# ---------------------------------------------------------------------------

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'published_at', 'created_at']
    list_filter = ['status']
    search_fields = ['title', 'author__email']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'created_at']
    search_fields = ['user__email', 'content']


@admin.register(BlogReaction)
class BlogReactionAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'reaction_type', 'created_at']
    list_filter = ['reaction_type']


# ---------------------------------------------------------------------------
# Other
# ---------------------------------------------------------------------------

@admin.register(Locations)
class LocationsAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'city', 'state', 'country']
    list_filter = ['type', 'country']
    search_fields = ['title', 'city', 'state']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['fullname', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['fullname', 'email']


@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'position']
    list_editable = ['is_active', 'position']
    list_filter = ['category', 'is_active']


@admin.register(AccountDeletionLog)
class AccountDeletionLogAdmin(admin.ModelAdmin):
    list_display = ['email', 'user_id', 'deleted_at', 'reason']
    search_fields = ['email']
    readonly_fields = ['user_id', 'email', 'firstname', 'lastname', 'phone', 'date_joined', 'deleted_at']


@admin.register(ProcessedStripeEvent)
class ProcessedStripeEventAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'event_type', 'processed_at']
    search_fields = ['event_id']
