from rest_framework import serializers
from .models import Listing, Booking, Review, Payment

class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ['id', 'title', 'description', 'location', 'price_per_night', 'owner', 'created_at']
        read_only_fields = ['id', 'created_at']

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'listing', 'user', 'check_in', 'check_out', 'guests', 'created_at']
        read_only_fields = ['id', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'listing', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'booking', 'transaction_id', 'chapa_reference', 'amount', 'currency', 'status', 'payment_method', 'created_at', 'updated_at']
        read_only_fields = ['id', 'transaction_id', 'created_at', 'updated_at']