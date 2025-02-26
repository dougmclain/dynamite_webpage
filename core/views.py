from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm
from honeypot.decorators import check_honeypot  # Add this import

# Create your views here.
def home(request):
    return render(request, 'core/home.html')

def location_detail(request, location_type, location_name=None, state_name=None):
    """
    View to handle location pages for both states and cities.
    
    Args:
        location_type: Either 'state' or 'city'
        location_name: Name of the location (state or city)
        state_name: Name of the state (only used for city pages)
    """
    # Dictionary of available locations with their image paths
    states = {
        'california': {
            'name': 'California',
            'image_path': 'images/locations/california.jpg',
        },
        'florida': {
            'name': 'Florida',
            'image_path': 'images/locations/florida.jpg',
        },
        'georgia': {
            'name': 'Georgia',
            'image_path': 'images/locations/georgia.jpg',
        },
        'hawaii': {
            'name': 'Hawaii',
            'image_path': 'images/locations/hawaii.jpg',
        },
        'illinois': {
            'name': 'Illinois',
            'image_path': 'images/locations/illinois.jpg',
        },
        'new-york': {
            'name': 'New York',
            'image_path': 'images/locations/new-york.jpg',
        },
        'oregon': {
            'name': 'Oregon',
            'image_path': 'images/locations/oregon.jpg',
        },
        'texas': {
            'name': 'Texas',
            'image_path': 'images/locations/texas.jpg',
        },
        'washington': {
            'name': 'Washington',
            'image_path': 'images/locations/washington.jpg',
        },
    }
    
    cities = {
        'san-francisco': {
            'name': 'San Francisco',
            'state': 'California',
            'image_path': 'images/locations/cities/san-francisco.jpg',
        },
        'miami': {
            'name': 'Miami',
            'state': 'Florida',
            'image_path': 'images/locations/cities/miami.jpg',
        },
        'chicago': {
            'name': 'Chicago',
            'state': 'Illinois',
            'image_path': 'images/locations/cities/chicago.jpg',
        },
        'portland': {
            'name': 'Portland',
            'state': 'Oregon',
            'image_path': 'images/locations/cities/portland.jpg',
        }
    }
    
    # Determine which location data to use based on URL parameters
    if location_type == 'state':
        location = states.get(location_name, {})
    else:  # City
        location = cities.get(location_name, {})
    
    context = {
        'location': location,
        'location_type': location_type,
    }
    
    return render(request, 'core/location_detail.html', context)

def financial_management(request):
    """
    View for the condo financial management page
    """
    return render(request, 'core/financial_management.html')

def about(request):
    """
    View for the about page
    """
    return render(request, 'core/about.html')

def blog(request):
    """
    View for the blog page
    """
    return render(request, 'core/blog.html')

@check_honeypot  # Add this decorator to protect the contact form
def contact(request):
    """
    View for the contact page and form handling
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        
        if form.is_valid():
            # Extract form data
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            comments = form.cleaned_data['comments']
            
            # Prepare email content
            subject = f'New Contact Form Submission from {first_name} {last_name}'
            message = f"""
            Contact Form Details:
            
            Name: {first_name} {last_name}
            Email: {email}
            Phone: {phone if phone else 'Not provided'}
            
            Message:
            {comments}
            """
            
            # Send email
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    ['info@hoafiscal.com'],
                    fail_silently=False,
                )
                messages.success(request, "Thank you for contacting us! Your message has been sent successfully.")
                return redirect('core:contact')
            except Exception as e:
                messages.error(request, f"Sorry, there was an error sending your message. Please try again later.")
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})