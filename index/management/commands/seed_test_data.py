"""
Management command to seed test data for Postman/Newman integration tests.

Usage:
    python manage.py seed_test_data          # Create all test data
    python manage.py seed_test_data --clean  # Remove test data first, then recreate
"""

import datetime
from django.core.management.base import BaseCommand

from index.models import Package, Destination, Event


# Plain string path stored in the DB — avoids filesystem writes so the command
# works regardless of MEDIA_ROOT configuration.
PLACEHOLDER_IMAGE_PATH = 'default.svg'


PACKAGES = [
    {
        'package_id': 'PKG-TEST-PARIS-001',
        'name': 'Paris City Break',
        'category': 'tourism',
        'vat': 10.00,
        'price_option': 'fixed',
        'fixed_price': 2500.00,
        'discount_price': '',
        'max_adult_limit': 6,
        'max_child_limit': 4,
        'date_from': datetime.date(2026, 6, 1),
        'date_to': datetime.date(2026, 12, 31),
        'duration': 7,
        'availability': 50,
        'virtual': 0,
        'country': 'France',
        'continent': 'Europe',
        'description': 'Explore the City of Light with guided tours of the Eiffel Tower, Louvre Museum, and Versailles Palace.',
        'destinations': 'Paris, Versailles',
        'services': 'Hotel, Transport, Meals, Guided Tours',
        'featured_events': 'Seine River Cruise, Wine Tasting',
        'featured_guests': '',
        'status': 'active',
    },
    {
        'package_id': 'PKG-TEST-BALI-002',
        'name': 'Bali Beach Retreat',
        'category': 'beach',
        'vat': 8.00,
        'price_option': 'fixed',
        'fixed_price': 3200.00,
        'discount_price': '',
        'max_adult_limit': 4,
        'max_child_limit': 3,
        'date_from': datetime.date(2026, 6, 1),
        'date_to': datetime.date(2026, 12, 31),
        'duration': 10,
        'availability': 30,
        'virtual': 0,
        'country': 'Indonesia',
        'continent': 'Asia',
        'description': 'Relax on pristine beaches, visit ancient temples, and enjoy world-class surfing in Bali.',
        'destinations': 'Kuta, Ubud, Seminyak',
        'services': 'Resort, Spa, Transport, Meals',
        'featured_events': 'Temple Tour, Surf Lessons',
        'featured_guests': '',
        'status': 'active',
    },
    {
        'package_id': 'PKG-TEST-SAFARI-003',
        'name': 'Kenya Safari Adventure',
        'category': 'adventure',
        'vat': 12.00,
        'price_option': 'fixed',
        'fixed_price': 4500.00,
        'discount_price': '',
        'max_adult_limit': 8,
        'max_child_limit': 4,
        'date_from': datetime.date(2026, 7, 1),
        'date_to': datetime.date(2026, 12, 31),
        'duration': 14,
        'availability': 20,
        'virtual': 0,
        'country': 'Kenya',
        'continent': 'Africa',
        'description': 'Witness the Great Migration and explore Masai Mara on this unforgettable safari adventure.',
        'destinations': 'Nairobi, Masai Mara, Lake Nakuru',
        'services': 'Lodge, Safari Vehicle, Guide, Meals',
        'featured_events': 'Game Drives, Hot Air Balloon',
        'featured_guests': '',
        'status': 'active',
    },
]


DESTINATIONS = [
    {
        'name': 'Paris',
        'country': 'France',
        'continent': 'Europe',
        'trips': 120,
        'description': 'The City of Light — world-famous for art, fashion, gastronomy, and culture.',
        'locations': 'Eiffel Tower, Louvre, Champs-Élysées, Montmartre',
        'services': 'Museum Tours, Dining, Shopping',
        'features': 'Historic landmarks, river cruises, wine tasting',
        'languages': 'French, English',
        'status': 'active',
    },
    {
        'name': 'Bali',
        'country': 'Indonesia',
        'continent': 'Asia',
        'trips': 85,
        'description': 'Tropical paradise known for beaches, rice terraces, temples, and vibrant culture.',
        'locations': 'Kuta Beach, Ubud Rice Terraces, Tanah Lot Temple',
        'services': 'Spa, Surfing, Temple Tours, Diving',
        'features': 'Beaches, temples, nightlife, wellness retreats',
        'languages': 'Bahasa Indonesia, English',
        'status': 'active',
    },
]


EVENTS = [
    {
        'name': 'Paris Fashion Week',
        'country': 'France',
        'continent': 'Europe',
        'description': 'One of the world\'s most prestigious fashion events held biannually in Paris.',
        'services': 'VIP Passes, Fashion Shows, Designer Meets',
        'status': 'active',
    },
    {
        'name': 'Bali Spirit Festival',
        'country': 'Indonesia',
        'continent': 'Asia',
        'description': 'Annual celebration of yoga, dance, and music in the heart of Bali.',
        'services': 'Yoga Classes, Dance Workshops, Music Performances',
        'status': 'active',
    },
]


class Command(BaseCommand):
    help = 'Seed database with test data for Postman/Newman integration tests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Remove existing test data (PKG-TEST-*) before seeding',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self._clean()

        self._seed_packages()
        self._seed_destinations()
        self._seed_events()

        self.stdout.write(self.style.SUCCESS('Test data seeded successfully.'))

    def _clean(self):
        count, _ = Package.objects.filter(package_id__startswith='PKG-TEST-').delete()
        self.stdout.write(f'  Removed {count} test package record(s)')

        count, _ = Destination.objects.filter(name__in=[d['name'] for d in DESTINATIONS]).delete()
        self.stdout.write(f'  Removed {count} test destination record(s)')

        count, _ = Event.objects.filter(name__in=[e['name'] for e in EVENTS]).delete()
        self.stdout.write(f'  Removed {count} test event record(s)')

    def _seed_packages(self):
        for pkg_data in PACKAGES:
            pkg, created = Package.objects.get_or_create(
                package_id=pkg_data['package_id'],
                defaults={**pkg_data, 'main_image': PLACEHOLDER_IMAGE_PATH},
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f'  Package {pkg.package_id}: {status}')

    def _seed_destinations(self):
        for dest_data in DESTINATIONS:
            dest, created = Destination.objects.get_or_create(
                name=dest_data['name'],
                country=dest_data['country'],
                defaults={**dest_data, 'main_image': PLACEHOLDER_IMAGE_PATH},
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f'  Destination {dest.name}: {status}')

    def _seed_events(self):
        for evt_data in EVENTS:
            evt, created = Event.objects.get_or_create(
                name=evt_data['name'],
                country=evt_data['country'],
                defaults={**evt_data, 'main_image': PLACEHOLDER_IMAGE_PATH},
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f'  Event {evt.name}: {status}')
