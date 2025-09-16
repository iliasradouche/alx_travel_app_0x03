from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listings.models import Listing, Booking, Review
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = "Seed the database with sample listings, bookings, and reviews data."

    def handle(self, *args, **options):
        # Clear existing data
        Review.objects.all().delete()
        Booking.objects.all().delete()
        Listing.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        # Create users
        users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="password123"
            )
            users.append(user)
        self.stdout.write(self.style.SUCCESS("Created test users."))

        # Create listings
        locations = ["Paris", "New York", "Tokyo"]
        listings = []
        for i in range(5):
            listing = Listing.objects.create(
                title=f"Listing {i+1}",
                description=f"Description for listing {i+1}",
                location=random.choice(locations),
                price_per_night=random.randint(50, 500),
                owner=random.choice(users)
            )
            listings.append(listing)
        self.stdout.write(self.style.SUCCESS("Created sample listings."))

        # Create bookings
        bookings = []
        for i in range(7):
            listing = random.choice(listings)
            user = random.choice(users)
            check_in = timezone.now().date()
            check_out = check_in + timezone.timedelta(days=random.randint(1, 10))
            booking = Booking.objects.create(
                listing=listing,
                user=user,
                check_in=check_in,
                check_out=check_out,
                guests=random.randint(1, 4)
            )
            bookings.append(booking)
        self.stdout.write(self.style.SUCCESS("Created sample bookings."))

        # Create reviews
        for i in range(10):
            listing = random.choice(listings)
            user = random.choice(users)
            rating = random.randint(1, 5)
            comment = f"This is review {i+1} for {listing.title}"
            # Enforce unique_together constraint for (listing, user)
            if not Review.objects.filter(listing=listing, user=user).exists():
                Review.objects.create(
                    listing=listing,
                    user=user,
                    rating=rating,
                    comment=comment
                )
        self.stdout.write(self.style.SUCCESS("Created sample reviews."))

        self.stdout.write(self.style.SUCCESS("Database seeding completed!"))