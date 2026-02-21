"""Add PersonalisedBooking and Carousel models.

PersonalisedBooking: custom event/cruise/holiday booking requests.
Carousel: admin-managed homepage banners with category-driven forms.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('index', '0001_add_split_payment_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonalisedBooking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(
                    choices=[
                        ('birthday_party', 'Birthday Party'),
                        ('wedding', 'Wedding'),
                        ('corporate_event', 'Corporate Event'),
                        ('anniversary', 'Anniversary'),
                        ('holiday', 'Holiday'),
                        ('cruise', 'Cruise'),
                        ('other', 'Other'),
                    ],
                    db_index=True,
                    max_length=30,
                )),
                ('date_from', models.DateField()),
                ('date_to', models.DateField()),
                ('duration_hours', models.PositiveIntegerField(blank=True, null=True, help_text='Duration in hours (for event/cruise bookings)')),
                ('duration_days', models.PositiveIntegerField(blank=True, null=True, help_text='Duration in days (for holiday bookings)')),
                ('cruise_type', models.CharField(
                    blank=True,
                    choices=[
                        ('luxury', 'Luxury'),
                        ('standard', 'Standard'),
                        ('budget', 'Budget'),
                        ('river', 'River Cruise'),
                        ('expedition', 'Expedition'),
                    ],
                    default='',
                    max_length=20,
                )),
                ('continent', models.CharField(blank=True, default='', max_length=100)),
                ('country', models.CharField(blank=True, default='', max_length=100)),
                ('state', models.CharField(blank=True, default='', max_length=200)),
                ('preferred_destination', models.CharField(blank=True, default='', max_length=255)),
                ('guests', models.PositiveIntegerField(default=0)),
                ('adults', models.PositiveIntegerField(default=1)),
                ('children', models.PositiveIntegerField(default=0)),
                ('catering', models.BooleanField(default=False)),
                ('bar_attendance', models.BooleanField(default=False)),
                ('decoration', models.BooleanField(default=False)),
                ('special_security', models.BooleanField(default=False)),
                ('photography', models.BooleanField(default=False)),
                ('entertainment', models.BooleanField(default=False)),
                ('additional_comments', models.TextField(blank=True, default='')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('reviewed', 'Reviewed'),
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected'),
                        ('completed', 'Completed'),
                    ],
                    db_index=True,
                    default='pending',
                    max_length=20,
                )),
                ('admin_notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='personalised_bookings',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Carousel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('subtitle', models.CharField(blank=True, default='', max_length=500)),
                ('image', models.ImageField(upload_to='carousel/')),
                ('cta_text', models.CharField(default='Explore', help_text='Call-to-action button text', max_length=100)),
                ('category', models.CharField(
                    choices=[
                        ('personalise', 'Personalise'),
                        ('cruise', 'Cruise'),
                        ('packages', 'Packages'),
                    ],
                    db_index=True,
                    help_text='Determines which booking form the app renders',
                    max_length=20,
                )),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('position', models.PositiveIntegerField(default=0, help_text='Display order (lower = first)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['position', '-created_at'],
            },
        ),
    ]
