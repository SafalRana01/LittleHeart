from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
import json
from datetime import timedelta
from .models import Booking, UserProfile
from django.utils import timezone
import logging
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .forms import RegistrationForm, ContactForm
from .models import UserProfile, Contact, Blog
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import login as django_login
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'frontend_littleheart/index.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        remember_me = request.POST.get('rememberMe')  
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            if remember_me:
                request.session.set_expiry(604800)  # 7 days
            else:
                request.session.set_expiry(0)  # Session ends on browser close
            messages.success(request, "Login successful!")
            return redirect(request.GET.get('next', 'home'))
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'frontend_littleheart/login.html')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            address = form.cleaned_data['address']
            password = form.cleaned_data['password']

            # Create user and profile directly
            user = User.objects.create_user(username=username, email=email, password=password)
            profile = UserProfile.objects.create(user=user, phone=phone, address=address)
            authenticated_user = authenticate(request, username=username, password=password)
            if authenticated_user:
                django_login(request, authenticated_user)
                messages.success(request, "Registration successful! You are now logged in.")
                return redirect('login')
            else:
                messages.error(request, "Authentication failed after registration.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()
    return render(request, 'frontend_littleheart/register.html', {'form': form})

def logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

def about(request):
    return render(request, 'frontend_littleheart/about.html')

def blog_list(request):
    blogs = Blog.objects.all()
    paginator = Paginator(blogs, 4)
    page = request.GET.get('page')
    try:
        blogs_page = paginator.page(page)
    except PageNotAnInteger:
        blogs_page = paginator.page(1)
    except EmptyPage:
        blogs_page = paginator.page(paginator.num_pages)
    return render(request, 'frontend_littleheart/blog.html', {'blogs': blogs_page})

def blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    other_blogs = Blog.objects.exclude(id=blog.id).order_by('-created_at')[:4]
    return render(request, 'frontend_littleheart/blog_detail.html', {'blog': blog, 'other_blogs': other_blogs})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            try:
                send_mail(
                    subject=f"New Contact Form Submission: {contact.subject}",
                    message=f"Name: {contact.name}\nEmail: {contact.email}\nPhone: {contact.phone or 'Not provided'}\nMessage: {contact.message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, "Thank you! Your message has been sent successfully.")
            except Exception as e:
                logger.error(f"Email sending failed for contact {contact.id}: {str(e)}")
                messages.error(request, "Message saved, but email sending failed. Please contact support.")
            return redirect('contact')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm()
    return render(request, 'frontend_littleheart/contact.html', {'form': form})

def grooming(request):
    return render(request, 'frontend_littleheart/grooming.html')

def regular_bathing(request):
    return render(request, 'frontend_littleheart/regular_bath.html')

def dog(request):
    return render(request, 'frontend_littleheart/dog.html')

def cat(request):
    return render(request, 'frontend_littleheart/cat.html')

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    if request.user.is_staff:
        all_bookings = Booking.objects.all().order_by('-created_at')
        return render(request, 'frontend_littleheart/my_bookings.html', {'bookings': all_bookings, 'is_staff': True})
    return render(request, 'frontend_littleheart/my_bookings.html', {'bookings': bookings})

@csrf_exempt
@login_required
def get_time_slots(request):
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'success': False, 'message': 'Date parameter is required'}, status=400)

    try:
        date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        today = timezone.now().date()
        max_date = today + timedelta(days=30)

        if date < today or date > max_date:
            return JsonResponse({'success': False, 'message': 'Please select a date within the next 30 days from today.'}, status=400)

        time_slots = []
        for hour in range(9, 17):  # 9 AM to 4 PM
            for minute in [0, 15, 30, 45]:
                if hour == 16 and minute > 0:
                    continue
                time_str = f"{hour:02d}:{minute:02d}"
                display_time = f"{hour % 12 or 12}:{minute:02d} {'PM' if hour >= 12 else 'AM'}"
                time_slots.append({'time': time_str, 'display': display_time})

        # Fetch booked times for the selected date
        booked_times = Booking.objects.filter(date_time__date=date).values_list('date_time__time', flat=True)
        available_slots = [slot for slot in time_slots if slot['time'] not in booked_times]

        return JsonResponse({'success': True, 'time_slots': available_slots})
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid date format'}, status=400)
    except Exception as e:
        logger.error(f"Error in get_time_slots: {str(e)}")
        return JsonResponse({'success': False, 'message': 'An unexpected error occurred'}, status=500)

@csrf_exempt
@login_required
def book_appointment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            full_name = data.get('full_name', user_profile.user.username)
            contact_no = data.get('contact_no', user_profile.phone or '')
            email = user_profile.user.email or settings.DEFAULT_FROM_EMAIL  # Fallback to default email

            pets = data.get('pets', [])
            if not pets:
                return JsonResponse({'success': False, 'message': 'At least one pet is required'}, status=400)

            service_type = data.get('service_type', 'washDry')  # Default to 'washDry' if not provided
            if service_type not in ['washDry', 'washTidy', 'fullGroom', 'puppy']:
                return JsonResponse({'success': False, 'message': 'Invalid service type'}, status=400)

            add_ons = data.get('add_ons', [])
            date_time_str = data.get('date_time')
            if not date_time_str:
                return JsonResponse({'success': False, 'message': 'Date and time are required'}, status=400)

            # Validate and calculate weight from the first pet
            weight = float(pets[0].get('weight', 0)) if pets and pets[0].get('weight') else 0.0
            total_price = calculate_total_price(service_type, add_ons, weight)

            # Parse and validate date_time
            date_time = timezone.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
            duration = get_service_duration(service_type, weight)
            if 'deshedding' in add_ons:
                duration += timedelta(minutes=15)
            end_time = date_time + duration

            # Check for overlapping bookings
            overlapping = Booking.objects.filter(
                date_time__lt=end_time, date_time__gte=date_time
            ).exists() or Booking.objects.filter(
                date_time__lte=date_time, date_time__gt=date_time - duration
            ).exists()
            if overlapping:
                return JsonResponse({'success': False, 'message': 'This date and time overlaps with an existing booking.'})

            # Date range validation
            today = timezone.now().date()
            max_date = today + timedelta(days=30)
            if date_time.date() < today or date_time.date() > max_date:
                return JsonResponse({'success': False, 'message': 'Please select a date within the next 30 days.'})

            # Create booking
            booking = Booking(
                user=request.user,
                full_name=full_name,
                contact_no=contact_no,
                email=email,
                pets=pets,
                service_type=service_type,
                add_ons=add_ons,
                date_time=date_time,
                total_price=total_price,
                status='pending'  # Default status
            )
            booking.save()

            # Send confirmation email
            try:
                send_booking_email(booking, email)
            except Exception as e:
                logger.error(f"Failed to send booking email for booking {booking.id}: {str(e)}")
                messages.error(request, "Booking saved, but email failed to send. Please check your email settings.")

            return JsonResponse({'success': True, 'message': 'Booking saved successfully'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
        except ValueError as e:
            return JsonResponse({'success': False, 'message': f'Invalid data format: {str(e)}'}, status=400)
        except Exception as e:
            logger.error(f"Error in book_appointment: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An unexpected error occurred'}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@login_required
def update_booking_status(request):
    if request.method == 'POST' and request.user.is_staff:
        booking_id = request.POST.get('booking_id')
        status = request.POST.get('status')
        try:
            booking = Booking.objects.get(id=booking_id)
            if status not in ['pending', 'confirmed', 'completed', 'cancelled']:
                return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)
            booking.status = status
            booking.save()
            send_status_update_email(booking, booking.email)
            return JsonResponse({'success': True, 'message': 'Status updated successfully'})
        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Booking not found'})
        except Exception as e:
            logger.error(f"Error updating booking status {booking_id}: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An error occurred while updating status'})
    return JsonResponse({'success': False, 'message': 'Invalid request or insufficient permissions'}, status=403)

def calculate_total_price(service_type, add_ons, weight):
    base_prices = {
        'washDry': {'XS': 500, 'S': 1000, 'M': 1500, 'L': 2000},
        'washTidy': {'XS': 500, 'S': 1000, 'M': 1500, 'L': 2000},
        'fullGroom': {'XS': 1500, 'S': 2000, 'M': 2500, 'L': 3500},
        'puppy': {'XS': 1500, 'S': 1500, 'M': 1500, 'L': 1500}
    }
    if weight < 5:
        size = 'XS'
    elif weight <= 11:
        size = 'S'
    elif weight <= 19:
        size = 'M'
    elif weight <= 30:
        size = 'L'
    else:
        size = 'Special'  # Handle weights > 30kg with custom pricing if needed
    total = base_prices.get(service_type, {}).get(size, 0)
    add_on_prices = {'deshedding': 200, 'specialShampoo': 200, 'nailClip': 200, 'analGland': 200, 'teethBrushing': 200}
    for add_on in add_ons:
        total += add_on_prices.get(add_on, 0)
    return total if total > 0 else 0  # Ensure non-negative price

def get_service_duration(service_type, weight):
    durations = {
        'washDry': {'XS': timedelta(minutes=45), 'S': timedelta(hours=1), 'M': timedelta(minutes=90), 'L': timedelta(hours=2)},
        'washTidy': {'XS': timedelta(minutes=45), 'S': timedelta(minutes=75), 'M': timedelta(minutes=90), 'L': timedelta(hours=2)},
        'fullGroom': {'XS': timedelta(minutes=90), 'S': timedelta(hours=2), 'M': timedelta(minutes=150), 'L': timedelta(minutes=210)},
        'puppy': {'XS': timedelta(minutes=90), 'S': timedelta(minutes=90), 'M': timedelta(minutes=90), 'L': timedelta(minutes=90)}
    }
    if weight < 5:
        size = 'XS'
    elif weight <= 11:
        size = 'S'
    elif weight <= 19:
        size = 'M'
    elif weight <= 30:
        size = 'L'
    else:
        size = 'Special'  # Default to a reasonable duration for weights > 30kg
    return durations.get(service_type, {}).get(size, timedelta(minutes=0))

def send_booking_email(booking, recipient_email):
    subject = 'Your Pet Grooming Booking Confirmation'
    message = f"""
    Dear {booking.full_name},

    Your booking has been successfully created with the following details:
    - Date & Time: {booking.date_time.strftime('%Y-%m-%d %I:%M %p')}
    - Service Type: {booking.service_type}
    - Total Price: Rs. {booking.total_price}
    - Status: {booking.status}
    - Pets: {json.dumps(booking.pets)}

    Thank you for choosing us!
    Little Heart Pet Shop
    """
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [recipient_email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Email sending failed for booking {booking.id}: {str(e)}")
        raise

def send_status_update_email(booking, recipient_email):
    subject = 'Your Pet Grooming Booking Status Update'
    message = f"""
    Dear {booking.full_name},

    The status of your booking has been updated to: {booking.status}

    Booking Details:
    - Date & Time: {booking.date_time.strftime('%Y-%m-%d %I:%M %p')}
    - Service Type: {booking.service_type}
    - Total Price: Rs. {booking.total_price}
    - Pets: {json.dumps(booking.pets)}

    Thank you!
    Little Heart Pet Shop
    """
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [recipient_email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Email sending failed for status update {booking.id}: {str(e)}")
        raise

@login_required
def get_user_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        return JsonResponse({
            'success': True,
            'full_name': user_profile.user.username,
            'contact_no': user_profile.phone or ''
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User profile not found'
        })

@login_required
@csrf_exempt
def check_booking_availability(request):
    if request.method == 'GET':
        date_str = request.GET.get('date')
        start_time = request.GET.get('start')
        duration = int(request.GET.get('duration', 0))  # Duration in minutes

        if not all([date_str, start_time, duration]):
            return JsonResponse({'success': False, 'message': 'Missing required parameters'}, status=400)

        try:
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            start_datetime = timezone.datetime.strptime(f"{date_str} {start_time}", '%Y-%m-%d %H:%M')
            end_datetime = start_datetime + timezone.timedelta(minutes=duration)

            # Check for overlapping bookings
            overlapping = Booking.objects.filter(
                date_time__lt=end_datetime,
                date_time__gte=start_datetime
            ).exists() or Booking.objects.filter(
                date_time__lte=start_datetime,
                date_time__gt=start_datetime - timezone.timedelta(minutes=duration)
            ).exists()

            return JsonResponse({'success': True, 'is_overlapping': overlapping})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid date or time format'}, status=400)
        except Exception as e:
            logger.error(f"Error in check_booking_availability: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An unexpected error occurred'}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
