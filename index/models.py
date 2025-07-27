# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.utils import timezone
import uuid



class CustomUserManager(BaseUserManager):
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
    email = models.EmailField(unique=True)
    firstname = models.CharField( max_length=100)
    lastname = models.CharField( max_length=100)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    activation_sent_at=models.DateTimeField(auto_now_add=True)
    status = models.CharField(_('Status'), max_length=50,default='active')
    saved_packages = models.ManyToManyField('Package', related_name='saved_by', blank=True)  # Add this line

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    

class CustomerProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'male'),
        ('female', 'female'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    address = models.CharField(_('Address'), max_length=255,blank=True,null=True)
    city= models.CharField(_('City'), max_length=100,blank=True,null=True)
    state= models.CharField(_('State'), max_length=100,blank=True,null=True)
    country = models.CharField(_('Country'), max_length=100,blank=True,null=True)
    phone = models.CharField(_('Phone'), max_length=20,blank=True,null=True)
    date_of_birth = models.DateField(_('Date of Birth'),blank=True,null=True)
    marital_status = models.CharField(_('Marital Status'), max_length=50,blank=True,null=True)
    profession= models.CharField(_('Profession'), max_length=100,blank=True,null=True)
    image = models.ImageField(upload_to='profile/images/',default='default.svg')
    status = models.CharField(_('Status'), max_length=50,default='active')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES,blank=True, null=True)


    def __str__(self):
        return self.user.email
    
    class Meta:
        ordering = ['-id']


class AdminProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    desgination = models.CharField(_('Desgination'), max_length=100)
    status= models.CharField(_('Status'), max_length=50,default='active')
    # Add fields specific to admin profile (e.g., basic information, roles, activity logs)

    def __str__(self):
        return self.user.email

class Locations(models.Model):
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Booking(models.Model):
    PURPOSE_CHOICES = [
        ('hotel', 'hotel'),
        ('tourism', 'tourism')
        
        # Add other purposes if needed
    ]
    GENDER_CHOICES = [
        ('male', 'male'),
        ('female', 'female'),
    ]
    booking_id = models.CharField(max_length=255, unique=True)
    package=models.CharField(max_length=255)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    cruise_type = models.TextField(blank=True, null=True)
    purpose = models.TextField()
    datefrom = models.DateField()
    dateto= models.DateField()
    continent = models.CharField(max_length=50)
    travelcountry = models.CharField(max_length=50)
    travelstate = models.CharField(max_length=200)  # To store multiple states as a single comma-separated string
    destinations = models.TextField()  # To store multiple destinations as a single comma-separated string
    guests = models.IntegerField(default=0)
    duration = models.IntegerField()
    adult = models.IntegerField()
    children = models.IntegerField(default=0)
    service = models.TextField()  # To store multiple services as a single comma-separated string
    price= models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    comment = models.TextField(blank=True, null=True)
    lastname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    profession = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    gender = models.CharField(max_length=10,blank=True, null=True)
    country = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    invoiced=models.BooleanField(default=False)
    invoice_id=models.CharField(max_length=255,blank=True,null=True)
    checkout_session_id=models.CharField(max_length=255,blank=True,null=True)
    payment_status=models.CharField(max_length=255,blank=True,null=True)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.purpose}"
    
    class Meta:
        ordering = ['-created_at']

    

class Contact(models.Model):
    fullname = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    status= models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.fullname} - {self.email}"
    
    class Meta:
        ordering = ['-created_at']
    
class Package(models.Model):
    package_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    vat = models.DecimalField(max_digits=5, decimal_places=2)
    price_option = models.CharField(max_length=255)
    fixed_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    discount_price=models.TextField(blank=True, null=True)
    max_adult_limit = models.IntegerField(blank=True, null=True)
    max_child_limit = models.IntegerField(blank=True, null=True)
    date_from = models.DateField()  # Date from
    date_to= models.DateField()
    duration = models.IntegerField()
    availability = models.IntegerField()
    virtual=models.IntegerField(default=0)
    country = models.CharField(max_length=255)
    continent= models.CharField(max_length=255)
    applications= models.IntegerField(default=0)
    submissions= models.IntegerField(default=0)
    description = models.TextField()
    main_image = models.ImageField(upload_to='package/main_images/')
    destinations = models.TextField()
    services = models.TextField()
    featured_events = models.TextField()
    featured_guests = models.TextField()
    status = models.CharField(max_length=50, default='active')
    bookings=models.ManyToManyField(Booking, related_name='packages', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('index:package-details', args=[str(self.package_id)])
    
    class Meta:
        ordering = ['-created_at']
        

class PackageImage(models.Model):
    package = models.ForeignKey(Package, related_name='package_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='package/images/')


class Invoice(models.Model):
    invoice_id = models.CharField(max_length=255, unique=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default='pending')
    items= models.TextField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    admin_percentage=models.DecimalField(max_digits=5, decimal_places=2)
    admin_fee = models.DecimalField(max_digits=10, decimal_places=2)
    total= models.DecimalField(max_digits=10, decimal_places=2)
    paid= models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.invoice_id
    
    class Meta:
        ordering = ['-created_at']
        
        
class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=255, unique=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    admin_fee = models.DecimalField(max_digits=10, decimal_places=2)
    vat= models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    paid= models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.payment_id
    
    class Meta:
        ordering = ['-created_at']

    
class Destination(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    continent= models.CharField(max_length=255)
    trips= models.IntegerField(default=0)
    description = models.TextField()
    main_image = models.ImageField(upload_to='destination/main_images/')
    locations = models.TextField()
    services = models.TextField()
    features = models.TextField()
    languages = models.TextField()
    status = models.CharField(max_length=50, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('index:destination-details', args=[str(self.id)])


class DestinationImage(models.Model):
    destination = models.ForeignKey(Destination, related_name='destination_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='destination/images/')

class Event(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    continent= models.CharField(max_length=255)
    description = models.TextField()
    main_image = models.ImageField(upload_to='destination/main_images/')
    services = models.TextField()
    status = models.CharField(max_length=50, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def get_absolute_url(self):
        return reverse('index:destination-details', args=[str(self.id)])

class EventImage(models.Model):
    event = models.ForeignKey(Event, related_name='event_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='event/images/')

class GuestImage(models.Model):
    package = models.ForeignKey(Package, related_name='guest_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='guest/images/')


class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email}'s Wallet (Balance: {self.balance})"

    def deposit(self, amount):
        """Add funds to wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.balance += amount
        self.save()
        return Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.DEPOSIT,
            status=Transaction.COMPLETED
        )

    def withdraw(self, amount):
        """Withdraw funds from wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.save()
        return Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.WITHDRAWAL,
            status=Transaction.COMPLETED
        )

    def transfer(self, recipient_wallet, amount):
        """Transfer funds to another wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        
        self.balance -= amount
        recipient_wallet.balance += amount
        self.save()
        recipient_wallet.save()
        
        transaction = Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.TRANSFER,
            recipient=recipient_wallet.user,
            status=Transaction.COMPLETED
        )
        return transaction


class Transaction(models.Model):
    # Transaction types
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    TRANSFER = 'transfer'
    
    # Transaction statuses
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    
    TRANSACTION_TYPE_CHOICES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
        (TRANSFER, 'Transfer'),
    ]
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    recipient = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transactions')
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    reference=models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} of {self.amount} by {self.wallet.user.email}"


# class Wallet(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wallet')
#     balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.user.email}'s Wallet (Balance: {self.balance})"

#     def deposit(self, amount):
#         """Add funds to wallet"""
#         if amount <= 0:
#             raise ValueError("Amount must be positive")
#         self.balance += amount
#         self.save()
#         return Transaction.objects.create(
#             wallet=self,
#             amount=amount,
#             transaction_type=Transaction.DEPOSIT,
#             status=Transaction.COMPLETED
#         )

#     def withdraw(self, amount):
#         """Withdraw funds from wallet"""
#         if amount <= 0:
#             raise ValueError("Amount must be positive")
#         if self.balance < amount:
#             raise ValueError("Insufficient funds")
#         self.balance -= amount
#         self.save()
#         return Transaction.objects.create(
#             wallet=self,
#             amount=amount,
#             transaction_type=Transaction.WITHDRAWAL,
#             status=Transaction.COMPLETED
#         )

#     def transfer(self, recipient_wallet, amount):
#         """Transfer funds to another wallet"""
#         if amount <= 0:
#             raise ValueError("Amount must be positive")
#         if self.balance < amount:
#             raise ValueError("Insufficient funds")
        
#         self.balance -= amount
#         recipient_wallet.balance += amount
#         self.save()
#         recipient_wallet.save()
        
#         transaction = Transaction.objects.create(
#             wallet=self,
#             amount=amount,
#             transaction_type=Transaction.TRANSFER,
#             recipient=recipient_wallet.user,
#             status=Transaction.COMPLETED
#         )
#         return transaction


# class Transaction(models.Model):
    # Transaction types
    # DEPOSIT = 'deposit'
    # WITHDRAWAL = 'withdrawal'
    # TRANSFER = 'transfer'
    
    # # Transaction statuses
    # PENDING = 'pending'
    # COMPLETED = 'completed'
    # FAILED = 'failed'
    
    # TRANSACTION_TYPE_CHOICES = [
    #     (DEPOSIT, 'Deposit'),
    #     (WITHDRAWAL, 'Withdrawal'),
    #     (TRANSFER, 'Transfer'),
    # ]
    
    # STATUS_CHOICES = [
    #     (PENDING, 'Pending'),
    #     (COMPLETED, 'Completed'),
    #     (FAILED, 'Failed'),
    # ]
    
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    # amount = models.DecimalField(max_digits=12, decimal_places=2)
    # transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    # status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    # recipient = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transactions')
    # stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    # description = models.TextField(blank=True, null=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    # def __str__(self):
    #     return f"{self.transaction_type.capitalize()} of {self.amount} by {self.wallet.user.email}"

    