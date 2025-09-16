from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
import requests
import uuid
from .models import Listing, Booking, Review, Payment
from .serializers import ListingSerializer, BookingSerializer, ReviewSerializer, PaymentSerializer
from .tasks import send_payment_confirmation_email, send_booking_confirmation_email

User = get_user_model()

class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing listings.
    Provides CRUD operations for Listing model.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        """Set the owner to the current user when creating a listing."""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """Get all bookings for a specific listing."""
        listing = self.get_object()
        bookings = listing.bookings.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for a specific listing."""
        listing = self.get_object()
        reviews = listing.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bookings.
    Provides CRUD operations for Booking model.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Set the user to the current user when creating a booking and send confirmation email."""
        booking = serializer.save(user=self.request.user)
        # Trigger asynchronous email task
        send_booking_confirmation_email.delay(booking.id)
    
    def get_queryset(self):
        """Filter bookings to show only user's own bookings unless user is staff."""
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def initiate_payment(self, request, pk=None):
        """Initiate payment for a booking using Chapa API"""
        try:
            booking = self.get_object()
            
            # Check if booking belongs to the user
            if booking.user != request.user:
                return Response(
                    {'error': 'You can only initiate payment for your own bookings'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if booking is already paid
            if booking.status == 'confirmed':
                return Response(
                    {'error': 'This booking is already confirmed and paid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate unique transaction reference
            tx_ref = f"booking_{booking.id}_{uuid.uuid4().hex[:8]}"
            
            # Prepare Chapa payment data
            payment_data = {
                'amount': str(booking.total_price),
                'currency': 'ETB',
                'email': request.user.email,
                'first_name': request.user.first_name or 'Customer',
                'last_name': request.user.last_name or 'User',
                'phone_number': getattr(request.user, 'phone', '0911000000'),
                'tx_ref': tx_ref,
                'callback_url': f"{request.build_absolute_uri('/api/payments/verify/')}",
                'return_url': f"{request.build_absolute_uri('/api/bookings/')}",
                'customization': {
                    'title': f'Payment for Booking #{booking.id}',
                    'description': f'Payment for {booking.listing.name}'
                }
            }
            
            # Make request to Chapa API
            headers = {
                'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://api.chapa.co/v1/transaction/initialize',
                json=payment_data,
                headers=headers
            )
            
            if response.status_code == 200:
                chapa_response = response.json()
                
                # Create Payment record
                payment = Payment.objects.create(
                    booking=booking,
                    amount=booking.total_price,
                    transaction_id=tx_ref,
                    payment_method='chapa',
                    status='pending'
                )
                
                # Update booking status
                booking.status = 'pending_payment'
                booking.save()
                
                return Response({
                    'message': 'Payment initiated successfully',
                    'payment_id': payment.id,
                    'checkout_url': chapa_response['data']['checkout_url'],
                    'transaction_reference': tx_ref
                }, status=status.HTTP_201_CREATED)
            
            else:
                return Response({
                    'error': 'Failed to initiate payment',
                    'details': response.json() if response.content else 'No response from payment gateway'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': 'An error occurred while initiating payment',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(booking__user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        """Verify payment status with Chapa API"""
        try:
            tx_ref = request.data.get('tx_ref')
            if not tx_ref:
                return Response(
                    {'error': 'Transaction reference is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find payment record
            try:
                payment = Payment.objects.get(transaction_id=tx_ref)
            except Payment.DoesNotExist:
                return Response(
                    {'error': 'Payment record not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user owns this payment
            if payment.booking.user != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'You can only verify your own payments'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verify with Chapa API
            headers = {
                'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'https://api.chapa.co/v1/transaction/verify/{tx_ref}',
                headers=headers
            )
            
            if response.status_code == 200:
                chapa_response = response.json()
                
                if chapa_response['status'] == 'success' and chapa_response['data']['status'] == 'success':
                    # Payment successful
                    payment.status = 'completed'
                    payment.save()
                    
                    # Update booking status
                    booking = payment.booking
                    booking.status = 'confirmed'
                    booking.save()
                    
                    # Send confirmation email asynchronously
                    send_payment_confirmation_email.delay(
                        payment.id,
                        booking.user.email,
                        booking.user.first_name or 'Customer'
                    )
                    
                    return Response({
                        'message': 'Payment verified successfully',
                        'payment_status': 'completed',
                        'booking_status': 'confirmed'
                    }, status=status.HTTP_200_OK)
                
                elif chapa_response['data']['status'] == 'failed':
                    # Payment failed
                    payment.status = 'failed'
                    payment.save()
                    
                    # Update booking status
                    booking = payment.booking
                    booking.status = 'cancelled'
                    booking.save()
                    
                    # Send failure email asynchronously
                    send_payment_failure_email.delay(
                        payment.id,
                        booking.user.email,
                        booking.user.first_name or 'Customer'
                    )
                    
                    return Response({
                        'message': 'Payment verification completed',
                        'payment_status': 'failed',
                        'booking_status': 'cancelled'
                    }, status=status.HTTP_200_OK)
                
                else:
                    # Payment still pending
                    return Response({
                        'message': 'Payment is still pending',
                        'payment_status': 'pending'
                    }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'error': 'Failed to verify payment with Chapa',
                    'details': response.json() if response.content else 'No response from payment gateway'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': 'An error occurred while verifying payment',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    Provides CRUD operations for Review model.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Set the user to the current user when creating a review."""
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        """Filter reviews to show only user's own reviews unless user is staff."""
        if self.request.user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(user=self.request.user)
