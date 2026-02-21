"""
Models for the Leisuretimez travel booking platform.

Contains models for users, profiles, packages, bookings, destinations,
events, invoices, payments, wallets, and transactions.
"""

import uuid
import logging

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction as db_transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User & Authentication
# ---------------------------------------------------------------------------

class CustomUserManager(BaseUserManager):
    """Manager for email-based custom user model."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the primary identifier."""

    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    activation_sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(_('Status'), max_length=50, default='active', db_index=True)
    saved_packages = models.ManyToManyField(
        'Package', related_name='saved_by', blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

class CustomerProfile(models.Model):
    """Extended profile for customer users."""

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    address = models.CharField(_('Address'), max_length=255, blank=True, null=True)
    city = models.CharField(_('City'), max_length=100, blank=True, null=True)
    state = models.CharField(_('State'), max_length=100, blank=True, null=True)
    country = models.CharField(_('Country'), max_length=100, blank=True, null=True)
    phone = models.CharField(_('Phone'), max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(_('Date of Birth'), blank=True, null=True)
    marital_status = models.CharField(
        _('Marital Status'), max_length=50, blank=True, null=True
    )
    profession = models.CharField(
        _('Profession'), max_length=100, blank=True, null=True
    )
    image = models.ImageField(upload_to='profile/images/', default='default.svg')
    status = models.CharField(_('Status'), max_length=50, default='active')
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, blank=True, null=True
    )

    def __str__(self):
        return self.user.email

    class Meta:
        ordering = ['-id']


class AdminProfile(models.Model):
    """Extended profile for admin users."""

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    designation = models.CharField(_('Designation'), max_length=100)
    status = models.CharField(_('Status'), max_length=50, default='active')

    def __str__(self):
        return self.user.email


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

class Locations(models.Model):
    """Geographic locations used for search and filtering."""

    title = models.CharField(max_length=255)
    type = models.CharField(max_length=255, db_index=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255, db_index=True)
    country = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Locations'


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

class Booking(models.Model):
    """Customer booking for a travel package."""

    PURPOSE_CHOICES = [
        ('hotel', 'Hotel'),
        ('tourism', 'Tourism'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    booking_id = models.CharField(max_length=255, unique=True, db_index=True)
    package = models.CharField(max_length=255, db_index=True)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, db_index=True)
    cruise_type = models.TextField(blank=True, null=True)
    purpose = models.TextField()
    datefrom = models.DateField()
    dateto = models.DateField()
    continent = models.CharField(max_length=50)
    travelcountry = models.CharField(max_length=50)
    travelstate = models.CharField(max_length=200)
    destinations = models.TextField()
    guests = models.IntegerField(default=0)
    duration = models.IntegerField()
    adult = models.IntegerField()
    children = models.IntegerField(default=0)
    service = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    comment = models.TextField(blank=True, null=True)
    lastname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    profession = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    invoiced = models.BooleanField(default=False)
    invoice_id = models.CharField(max_length=255, blank=True, null=True)
    checkout_session_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    payment_status = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    payment_method = models.CharField(
        max_length=10,
        choices=[
            ('wallet', 'Wallet'),
            ('stripe', 'Stripe'),
            ('split', 'Split (Wallet + Stripe)'),
        ],
        blank=True,
        default='',
    )
    wallet_amount_paid = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    stripe_amount_due = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    wallet_transaction_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text='UUID of the wallet Transaction record for wallet/split payments',
    )
    # Cancellation
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, default='')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    refund_status = models.CharField(
        max_length=20,
        choices=[
            ('', 'N/A'),
            ('pending', 'Pending'),
            ('processed', 'Processed'),
            ('denied', 'Denied'),
        ],
        blank=True, default='',
    )

    # Promo code
    promo_code = models.ForeignKey(
        'PromoCode', on_delete=models.SET_NULL, null=True, blank=True,
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=50, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.purpose}"

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

class Contact(models.Model):
    """Contact form submission."""

    fullname = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.fullname} - {self.email}"

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

class Package(models.Model):
    """Travel package offered to customers."""

    package_id = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=255, db_index=True)
    vat = models.DecimalField(max_digits=5, decimal_places=2)
    price_option = models.CharField(max_length=255)
    fixed_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    discount_price = models.TextField(blank=True, null=True)
    max_adult_limit = models.IntegerField(blank=True, null=True)
    max_child_limit = models.IntegerField(blank=True, null=True)
    date_from = models.DateField()
    date_to = models.DateField()
    duration = models.IntegerField()
    availability = models.IntegerField()
    virtual = models.IntegerField(default=0)
    country = models.CharField(max_length=255, db_index=True)
    continent = models.CharField(max_length=255, db_index=True)
    applications = models.IntegerField(default=0)
    submissions = models.IntegerField(default=0)
    description = models.TextField()
    main_image = models.ImageField(upload_to='package/main_images/')
    destinations = models.TextField()
    services = models.TextField()
    featured_events = models.TextField()
    featured_guests = models.TextField()
    status = models.CharField(max_length=50, default='active', db_index=True)
    bookings = models.ManyToManyField(
        Booking, related_name='packages', blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('index:api-package-details', args=[str(self.package_id)])

    class Meta:
        ordering = ['-created_at']


class PackageImage(models.Model):
    """Additional images for a package."""

    package = models.ForeignKey(
        Package, related_name='package_images', on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='package/images/')

    def __str__(self):
        return f"Image for {self.package.name}"


# ---------------------------------------------------------------------------
# Invoices & Payments
# ---------------------------------------------------------------------------

class Invoice(models.Model):
    """Invoice generated for a booking."""

    invoice_id = models.CharField(max_length=255, unique=True, db_index=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, db_index=True)
    status = models.CharField(max_length=50, default='pending', db_index=True)
    items = models.TextField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    admin_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    admin_fee = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.invoice_id

    class Meta:
        ordering = ['-created_at']


class Payment(models.Model):
    """Payment record for an invoice."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=255, unique=True, db_index=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=50, default='pending', db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    admin_fee = models.DecimalField(max_digits=10, decimal_places=2)
    vat = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.payment_id

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------------------------------
# Destinations
# ---------------------------------------------------------------------------

class Destination(models.Model):
    """Travel destination with details and images."""

    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    continent = models.CharField(max_length=255)
    trips = models.IntegerField(default=0)
    description = models.TextField()
    main_image = models.ImageField(upload_to='destination/main_images/')
    locations = models.TextField()
    services = models.TextField()
    features = models.TextField()
    languages = models.TextField()
    status = models.CharField(max_length=50, default='active', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('index:destination-details', args=[str(self.id)])


class DestinationImage(models.Model):
    """Additional images for a destination."""

    destination = models.ForeignKey(
        Destination, related_name='destination_images', on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='destination/images/')

    def __str__(self):
        return f"Image for {self.destination.name}"


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class Event(models.Model):
    """Event or attraction at a destination."""

    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    continent = models.CharField(max_length=255)
    description = models.TextField()
    main_image = models.ImageField(upload_to='event/main_images/')
    services = models.TextField()
    status = models.CharField(max_length=50, default='active', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('index:event-details', args=[str(self.id)])


class EventImage(models.Model):
    """Additional images for an event."""

    event = models.ForeignKey(
        Event, related_name='event_images', on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='event/images/')

    def __str__(self):
        return f"Image for {self.event.name}"


class GuestImage(models.Model):
    """Featured guest images for a package."""

    package = models.ForeignKey(
        Package, related_name='guest_images', on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='guest/images/')

    def __str__(self):
        return f"Guest image for {self.package.name}"


# ---------------------------------------------------------------------------
# Wallet & Transactions
# ---------------------------------------------------------------------------

class Wallet(models.Model):
    """User wallet for managing funds."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='wallet'
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return f"{self.user.email}'s Wallet (Balance: {self.balance})"

    def deposit(self, amount):
        """Add funds to wallet within a database transaction.

        Uses select_for_update() to prevent concurrent balance corruption.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.pk)
            wallet.balance += amount
            wallet.save()
            self.balance = wallet.balance
            return Transaction.objects.create(
                wallet=self,
                amount=amount,
                transaction_type=Transaction.DEPOSIT,
                status=Transaction.COMPLETED,
            )

    def withdraw(self, amount):
        """Withdraw funds from wallet within a database transaction.

        Uses select_for_update() to prevent concurrent balance corruption.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.pk)
            if wallet.balance < amount:
                raise ValueError("Insufficient funds")
            wallet.balance -= amount
            wallet.save()
            self.balance = wallet.balance
            return Transaction.objects.create(
                wallet=self,
                amount=amount,
                transaction_type=Transaction.WITHDRAWAL,
                status=Transaction.COMPLETED,
            )

    def transfer(self, recipient_wallet, amount):
        """Transfer funds to another wallet within a database transaction.

        Uses select_for_update() to prevent concurrent balance corruption.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        with db_transaction.atomic():
            sender = Wallet.objects.select_for_update().get(pk=self.pk)
            recipient = Wallet.objects.select_for_update().get(pk=recipient_wallet.pk)
            if sender.balance < amount:
                raise ValueError("Insufficient funds")
            sender.balance -= amount
            recipient.balance += amount
            sender.save()
            recipient.save()
            self.balance = sender.balance
            recipient_wallet.balance = recipient.balance
            return Transaction.objects.create(
                wallet=self,
                amount=amount,
                transaction_type=Transaction.TRANSFER,
                recipient=recipient_wallet.user,
                status=Transaction.COMPLETED,
            )


class Transaction(models.Model):
    """Record of a wallet transaction (deposit, withdrawal, or transfer)."""

    # Transaction types
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    TRANSFER = 'transfer'

    TRANSACTION_TYPE_CHOICES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
        (TRANSFER, 'Transfer'),
    ]

    # Transaction statuses
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name='transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPE_CHOICES
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=PENDING
    )
    recipient = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='received_transactions'
    )
    stripe_payment_intent_id = models.CharField(
        max_length=100, blank=True, null=True, db_index=True
    )
    reference = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.transaction_type.capitalize()} of {self.amount} "
            f"by {self.wallet.user.email}"
        )

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

class Review(models.Model):
    """User review for a completed travel package."""

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='reviews'
    )
    package = models.ForeignKey(
        Package, on_delete=models.CASCADE, related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'package')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.package.name} ({self.rating}/5)"


# ---------------------------------------------------------------------------
# Promo Codes
# ---------------------------------------------------------------------------

class PromoCode(models.Model):
    """Promotional discount code for bookings."""

    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_uses = models.IntegerField(default=0, help_text='0 = unlimited')
    current_uses = models.IntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.discount_type}: {self.discount_value})"

    def is_valid(self):
        """Check if this promo code is currently valid."""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_to:
            return False
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False
        return True

    def calculate_discount(self, order_amount):
        """Return the discount amount for the given order total."""
        from decimal import Decimal as D
        if order_amount < self.min_order_amount:
            return D('0.00')
        if self.discount_type == 'percentage':
            return (self.discount_value / 100 * order_amount).quantize(D('0.01'))
        return min(self.discount_value, order_amount)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class Notification(models.Model):
    """In-app notification for a user."""

    TYPE_CHOICES = [
        ('booking_confirmed', 'Booking Confirmed'),
        ('payment_received', 'Payment Received'),
        ('trip_reminder', 'Trip Reminder'),
        ('booking_cancelled', 'Booking Cancelled'),
        ('refund_processed', 'Refund Processed'),
        ('promo', 'Promotion'),
        ('system', 'System'),
        ('new_blog_post', 'New Blog Post'),
        ('blog_comment', 'Blog Comment'),
        ('blog_reaction', 'Blog Reaction'),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='notifications', db_index=True
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    booking = models.ForeignKey(
        Booking, on_delete=models.SET_NULL, null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type}: {self.title} ({self.user.email})"


# ---------------------------------------------------------------------------
# Support Tickets
# ---------------------------------------------------------------------------

class SupportTicket(models.Model):
    """Customer support ticket."""

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='support_tickets', db_index=True
    )
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.pk} {self.subject} ({self.status})"


class SupportMessage(models.Model):
    """Message within a support ticket conversation."""

    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message on #{self.ticket.pk} by {self.sender.email}"


# ---------------------------------------------------------------------------
# Account Deletion Audit
# ---------------------------------------------------------------------------

class ProcessedStripeEvent(models.Model):
    """Tracks processed Stripe webhook events for idempotency.

    Prevents duplicate processing of the same webhook event.
    """

    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-processed_at']

    def __str__(self):
        return f"{self.event_type}: {self.event_id}"


class AccountDeletionLog(models.Model):
    """Audit log preserving original user identity after account soft-deletion.

    This record is internal-only and not exposed via the API.
    It ensures the business can trace deleted accounts back to their
    original owner for disputes, chargebacks, or legal compliance.
    """

    user_id = models.IntegerField(help_text='Original PK of the deleted user')
    email = models.EmailField()
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, default='')
    date_joined = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, default='User-requested account deletion')
    wallet_balance_at_deletion = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
    )

    class Meta:
        ordering = ['-deleted_at']

    def __str__(self):
        return f"Deleted: {self.email} (user_id={self.user_id}) on {self.deleted_at}"


# ---------------------------------------------------------------------------
# Blog
# ---------------------------------------------------------------------------

class BlogPost(models.Model):
    """Blog post published by staff/admin."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='blog_posts', db_index=True
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True, default='')
    cover_image = models.ImageField(upload_to='blog/covers/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', db_index=True)
    tags = models.CharField(max_length=500, blank=True, default='',
                            help_text='Comma-separated tags')
    published_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title


class BlogComment(models.Model):
    """User comment on a blog post."""

    post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE, related_name='comments', db_index=True
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='blog_comments'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='replies',
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.email} on '{self.post.title}'"


class BlogReaction(models.Model):
    """User reaction on a blog post (like, love, etc.)."""

    REACTION_CHOICES = [
        ('like', 'Like'),
        ('love', 'Love'),
        ('insightful', 'Insightful'),
        ('celebrate', 'Celebrate'),
    ]

    post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE, related_name='reactions', db_index=True
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='blog_reactions'
    )
    reaction_type = models.CharField(max_length=15, choices=REACTION_CHOICES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} {self.reaction_type}d '{self.post.title}'"


# ---------------------------------------------------------------------------
# Personalised Booking
# ---------------------------------------------------------------------------

class PersonalisedBooking(models.Model):
    """Custom event/cruise booking request submitted via the mobile app or web."""

    EVENT_TYPE_CHOICES = [
        ('birthday_party', 'Birthday Party'),
        ('wedding', 'Wedding'),
        ('corporate_event', 'Corporate Event'),
        ('anniversary', 'Anniversary'),
        ('holiday', 'Holiday'),
        ('cruise', 'Cruise'),
        ('other', 'Other'),
    ]

    CRUISE_TYPE_CHOICES = [
        ('luxury', 'Luxury'),
        ('standard', 'Standard'),
        ('budget', 'Budget'),
        ('river', 'River Cruise'),
        ('expedition', 'Expedition'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='personalised_bookings', db_index=True,
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES, db_index=True)
    date_from = models.DateField()
    date_to = models.DateField()
    duration_hours = models.PositiveIntegerField(
        blank=True, null=True,
        help_text='Duration in hours (for event/cruise bookings)',
    )
    duration_days = models.PositiveIntegerField(
        blank=True, null=True,
        help_text='Duration in days (for holiday bookings)',
    )
    cruise_type = models.CharField(
        max_length=20, choices=CRUISE_TYPE_CHOICES, blank=True, default='',
    )
    continent = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=200, blank=True, default='')
    preferred_destination = models.CharField(max_length=255, blank=True, default='')
    guests = models.PositiveIntegerField(default=0)
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)

    # Services (stored as comma-separated values)
    catering = models.BooleanField(default=False)
    bar_attendance = models.BooleanField(default=False)
    decoration = models.BooleanField(default=False)
    special_security = models.BooleanField(default=False)
    photography = models.BooleanField(default=False)
    entertainment = models.BooleanField(default=False)

    additional_comments = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True,
    )
    admin_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.event_type} ({self.status})"


# ---------------------------------------------------------------------------
# Carousel
# ---------------------------------------------------------------------------

class Carousel(models.Model):
    """Homepage carousel/banner item for the mobile app."""

    CATEGORY_CHOICES = [
        ('personalise', 'Personalise'),
        ('cruise', 'Cruise'),
        ('packages', 'Packages'),
    ]

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=500, blank=True, default='')
    image = models.ImageField(upload_to='carousel/')
    cta_text = models.CharField(
        max_length=100, default='Explore',
        help_text='Call-to-action button text',
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, db_index=True,
        help_text='Determines which booking form the app renders',
    )
    is_active = models.BooleanField(default=True, db_index=True)
    position = models.PositiveIntegerField(
        default=0,
        help_text='Display order (lower = first)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.category})"
