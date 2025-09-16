from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Payment, Booking

User = get_user_model()

@shared_task
def send_booking_confirmation_email(booking_id):
    """
    Send booking confirmation email to the user after booking creation.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        user = booking.user
        
        subject = f'Booking Confirmation - Booking #{booking.id}'
        message = f"""
        Dear {user.first_name or user.username},
        
        Your booking has been confirmed!
        
        Booking Details:
        - Listing: {booking.listing.title}
        - Location: {booking.listing.location}
        - Check-in: {booking.check_in}
        - Check-out: {booking.check_out}
        - Guests: {booking.guests}
        - Total Price: ${booking.total_price}
        
        Thank you for choosing ALX Travel App!
        
        Best regards,
        ALX Travel Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return f"Booking confirmation email sent successfully to {user.email}"
        
    except Booking.DoesNotExist:
        return f"Booking with ID {booking_id} not found"
    except Exception as e:
        return f"Error sending booking confirmation email: {str(e)}"



@shared_task
def send_payment_confirmation_email(payment_id):
    """
    Send payment confirmation email to the user after successful payment.
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        booking = payment.booking
        user = booking.user
        
        subject = f'Payment Confirmation - Booking #{booking.id}'
        message = f"""
        Dear {user.first_name or user.username},
        
        Your payment has been successfully processed!
        
        Booking Details:
        - Listing: {booking.listing.title}
        - Location: {booking.listing.location}
        - Check-in: {booking.check_in}
        - Check-out: {booking.check_out}
        - Guests: {booking.guests}
        - Amount Paid: {payment.amount} {payment.currency}
        - Transaction ID: {payment.transaction_id}
        
        Thank you for choosing ALX Travel App!
        
        Best regards,
        ALX Travel Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return f"Email sent successfully to {user.email}"
        
    except Payment.DoesNotExist:
        return f"Payment with ID {payment_id} not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"

@shared_task
def send_payment_failure_email(payment_id):
    """
    Send payment failure notification email to the user.
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        booking = payment.booking
        user = booking.user
        
        subject = f'Payment Failed - Booking #{booking.id}'
        message = f"""
        Dear {user.first_name or user.username},
        
        Unfortunately, your payment could not be processed.
        
        Booking Details:
        - Listing: {booking.listing.title}
        - Amount: {payment.amount} {payment.currency}
        - Transaction ID: {payment.transaction_id}
        
        Please try again or contact our support team for assistance.
        
        Best regards,
        ALX Travel Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return f"Failure notification sent to {user.email}"
        
    except Payment.DoesNotExist:
        return f"Payment with ID {payment_id} not found"
    except Exception as e:
        return f"Error sending failure email: {str(e)}"