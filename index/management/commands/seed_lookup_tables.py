"""
Management command to seed EventType, CruiseType, and ServiceCatalog tables.

Usage:
    python manage.py seed_lookup_tables
"""

from django.core.management.base import BaseCommand

from index.models import CruiseType, EventType, ServiceCatalog


class Command(BaseCommand):
    help = "Seed default EventType, CruiseType, and ServiceCatalog entries"

    def handle(self, *args, **options):
        self._seed_event_types()
        self._seed_cruise_types()
        self._seed_service_catalog()
        self.stdout.write(self.style.SUCCESS("Lookup tables seeded successfully."))

    def _seed_event_types(self):
        event_types = [
            {"slug": "birthday_party", "name": "Birthday Party", "description": "Celebrate a birthday in style", "icon": "cake", "position": 1},
            {"slug": "wedding", "name": "Wedding", "description": "Plan your dream wedding", "icon": "favorite", "position": 2},
            {"slug": "corporate_event", "name": "Corporate Event", "description": "Conferences, team building, and corporate retreats", "icon": "business", "position": 3},
            {"slug": "anniversary", "name": "Anniversary", "description": "Celebrate years of love and togetherness", "icon": "celebration", "position": 4},
            {"slug": "holiday", "name": "Holiday", "description": "Plan a relaxing holiday getaway", "icon": "beach_access", "position": 5},
            {"slug": "cruise", "name": "Cruise", "description": "Set sail on the cruise of a lifetime", "icon": "directions_boat", "position": 6},
            {"slug": "other", "name": "Other", "description": "Custom event or special occasion", "icon": "star", "position": 7},
        ]
        created = 0
        for et in event_types:
            _, was_created = EventType.objects.get_or_create(slug=et["slug"], defaults=et)
            if was_created:
                created += 1
        self.stdout.write(f"  EventType: {created} created, {len(event_types) - created} already existed")

    def _seed_cruise_types(self):
        cruise_types = [
            {"slug": "luxury", "name": "Luxury", "description": "Premium luxury cruise experience", "icon": "diamond", "position": 1},
            {"slug": "adventure", "name": "Adventure", "description": "Thrilling adventure and expedition cruises", "icon": "explore", "position": 2},
            {"slug": "family", "name": "Family", "description": "Family-friendly cruises with activities for all ages", "icon": "family_restroom", "position": 3},
            {"slug": "romantic", "name": "Romantic", "description": "Romantic getaways and couples cruises", "icon": "favorite", "position": 4},
            {"slug": "business", "name": "Business", "description": "Business and corporate cruise packages", "icon": "business_center", "position": 5},
            {"slug": "cultural", "name": "Cultural", "description": "Cultural and heritage cruise experiences", "icon": "museum", "position": 6},
            {"slug": "river", "name": "River Cruise", "description": "Scenic river cruise journeys", "icon": "water", "position": 7},
            {"slug": "expedition", "name": "Expedition", "description": "Remote expedition and polar cruises", "icon": "terrain", "position": 8},
            {"slug": "standard", "name": "Standard", "description": "Standard cruise packages", "icon": "directions_boat", "position": 9},
            {"slug": "budget", "name": "Budget", "description": "Affordable budget-friendly cruises", "icon": "savings", "position": 10},
        ]
        created = 0
        for ct in cruise_types:
            _, was_created = CruiseType.objects.get_or_create(slug=ct["slug"], defaults=ct)
            if was_created:
                created += 1
        self.stdout.write(f"  CruiseType: {created} created, {len(cruise_types) - created} already existed")

    def _seed_service_catalog(self):
        services = [
            {"slug": "catering", "name": "Catering", "category": "catering", "description": "Full catering and meal services", "icon": "restaurant", "position": 1},
            {"slug": "bar-service", "name": "Bar Service", "category": "beverage", "description": "Full bar and beverage service", "icon": "local_bar", "position": 2},
            {"slug": "decoration", "name": "Decoration", "category": "decor", "description": "Event decoration and styling", "icon": "palette", "position": 3},
            {"slug": "special-security", "name": "Special Security", "category": "security", "description": "Private security and VIP protection", "icon": "security", "position": 4},
            {"slug": "photography", "name": "Photography", "category": "media", "description": "Professional photography coverage", "icon": "camera_alt", "position": 5},
            {"slug": "entertainment", "name": "Entertainment", "category": "entertainment", "description": "Live music, DJs, and entertainment", "icon": "music_note", "position": 6},
            {"slug": "videography", "name": "Videography", "category": "media", "description": "Professional video coverage", "icon": "videocam", "position": 7},
            {"slug": "floral-arrangements", "name": "Floral Arrangements", "category": "decor", "description": "Custom floral design and arrangements", "icon": "local_florist", "position": 8},
            {"slug": "transport", "name": "Transport", "category": "transport", "description": "Guest transportation and transfers", "icon": "airport_shuttle", "position": 9},
            {"slug": "accommodation", "name": "Accommodation", "category": "accommodation", "description": "Guest lodging and accommodation", "icon": "hotel", "position": 10},
            {"slug": "event-planning", "name": "Event Planning", "category": "other", "description": "Full event planning and coordination", "icon": "event", "position": 11},
            {"slug": "spa-wellness", "name": "Spa & Wellness", "category": "other", "description": "Spa treatments and wellness packages", "icon": "spa", "position": 12},
        ]
        created = 0
        for svc in services:
            _, was_created = ServiceCatalog.objects.get_or_create(slug=svc["slug"], defaults=svc)
            if was_created:
                created += 1
        self.stdout.write(f"  ServiceCatalog: {created} created, {len(services) - created} already existed")
