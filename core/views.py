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
            'intro': "From coastal condo towers to inland planned communities, California HOAs operate under some of the most detailed common-interest laws in the country. Dynamite Management gives California boards dedicated accounting, fraud protection, and financial oversight built for that complexity.",
            'law': "California community associations are governed by the Davis-Stirling Common Interest Development Act, which sets strict rules for annual budgets, reserve funding, owner disclosures, and assessment collection. Boards must distribute a pro forma operating budget and reserve funding disclosure each year and complete reserve studies on a regular cycle. We keep your financial statements, reserve reporting, and required disclosures accurate and on schedule so your California board stays compliant.",
        },
        'florida': {
            'name': 'Florida',
            'image_path': 'images/locations/florida.jpg',
            'intro': "Florida's condominium and HOA communities — especially along the coast — face the nation's most demanding financial and structural-reserve requirements. Dynamite Management helps Florida boards stay funded, compliant, and audit-ready.",
            'law': "Florida condominiums fall under Chapter 718 and HOAs under Chapter 720 of the Florida Statutes. Following the 2021 Surfside collapse, the state now requires milestone structural inspections and Structural Integrity Reserve Studies (SIRS) for many condominium buildings, with mandatory reserve funding that boards can no longer waive. We handle the reserve accounting, financial reporting, and Form 1120-H tax preparation that keep your Florida association on the right side of these rules.",
        },
        'georgia': {
            'name': 'Georgia',
            'image_path': 'images/locations/georgia.jpg',
            'intro': "Georgia's fast-growing metro and suburban communities depend on sound association finances to protect property values. Dynamite Management provides Georgia HOA and condo boards with professional accounting and fraud-protection controls.",
            'law': "Georgia associations are typically governed by the Georgia Property Owners' Association Act (O.C.G.A. § 44-3-220) or the Georgia Condominium Act, depending on how the community is organized. These statutes shape assessment collection, lien rights, and financial recordkeeping obligations. We maintain the accurate records and reporting your board needs to enforce assessments and stay transparent with owners.",
        },
        'hawaii': {
            'name': 'Hawaii',
            'image_path': 'images/locations/hawaii.jpg',
            'intro': "Hawaii's condominium associations manage high-value property in a unique island market, where careful financial stewardship is essential. Dynamite Management delivers islands-wide associations dependable accounting and reserve oversight.",
            'law': "Hawaii condominiums are governed by HRS Chapter 514B (the Condominium Property Act), with planned community associations covered under HRS Chapter 421J. The law sets requirements for budgets, reserve studies, and reserve funding so buildings stay maintainable over time. We manage your financial statements, reserve reporting, and tax filings so your Hawaii board can meet those obligations with confidence.",
        },
        'illinois': {
            'name': 'Illinois',
            'image_path': 'images/locations/illinois.jpg',
            'intro': "From Chicago high-rises to suburban townhome communities, Illinois associations operate under detailed condominium and common-interest statutes. Dynamite Management keeps Illinois boards' books accurate and their owners informed.",
            'law': "Illinois condominiums are governed by the Condominium Property Act (765 ILCS 605), and many non-condo communities by the Common Interest Community Association Act (765 ILCS 160). These laws give owners broad rights to inspect financial records and require disciplined budgeting and reserve practices. We provide the transparent financial statements and recordkeeping that keep your association compliant and owner requests easy to answer.",
        },
        'new-york': {
            'name': 'New York',
            'image_path': 'images/locations/new-york.jpg',
            'intro': "New York's condos and co-ops carry significant financial responsibility in one of the country's most demanding real-estate markets. Dynamite Management supports New York boards with rigorous accounting and reserve oversight.",
            'law': "New York condominiums are formed under the Condominium Act (Article 9-B of the Real Property Law), while cooperatives operate as corporations with their own financial and tax considerations. Both require careful budgeting, reserve funding, and clear financial reporting to owners and lenders. We handle the accounting, reserve tracking, and association tax preparation that keep your New York community financially sound.",
        },
        'oregon': {
            'name': 'Oregon',
            'image_path': 'images/locations/oregon.jpg',
            'intro': "Oregon's planned communities and condominiums are required to plan ahead financially — and Dynamite Management helps Oregon boards do exactly that with dependable accounting and reserve reporting.",
            'law': "Oregon associations are governed by the Oregon Planned Community Act (ORS Chapter 94) and the Oregon Condominium Act (ORS Chapter 100), which require reserve studies and ongoing reserve funding for most communities, along with annual financial information for owners. We keep your reserve schedules, financial statements, and filings accurate so your association meets Oregon's funding requirements.",
        },
        'texas': {
            'name': 'Texas',
            'image_path': 'images/locations/texas.jpg',
            'intro': "Texas's fast-growing HOA and condo communities need finances that scale with them. Dynamite Management gives Texas boards professional accounting, collections support, and fraud protection.",
            'law': "Texas HOAs are governed by the Texas Residential Property Owners Protection Act (Chapter 209 of the Property Code), and condominiums by the Texas Uniform Condominium Act (Chapter 82). These statutes set rules for assessment collection, owner notice, and records access. We maintain the financial records and reporting your board needs to collect assessments fairly and keep owners informed.",
        },
        'washington': {
            'name': 'Washington',
            'image_path': 'images/locations/washington.jpg',
            'intro': "Washington associations are in the middle of a major legal transition, and Dynamite Management helps Washington boards — especially self-managed condos — stay compliant and financially healthy.",
            'law': "Washington's common-interest communities are increasingly governed by the Washington Uniform Common Interest Ownership Act (WUCIOA, RCW 64.90), which expands requirements for budgets, reserve studies, and reserve funding — with key provisions reaching more associations by 2028. Older communities may still fall under RCW 64.34 (condominiums) or 64.38 (HOAs). We keep your reserve studies, financial statements, and disclosures aligned with WUCIOA so your board is ready.",
        },
    }

    cities = {
        'san-francisco': {
            'name': 'San Francisco',
            'state': 'California',
            'image_path': 'images/locations/cities/san-francisco.jpg',
            'intro': "San Francisco's dense condominium market and high property values make professional association finances essential. Dynamite Management serves San Francisco condo and HOA boards with dedicated accounting and oversight.",
            'law': "San Francisco associations operate under California's Davis-Stirling Common Interest Development Act, with its strict budget, reserve-funding, and annual disclosure requirements — and the city's older, high-value buildings make reserve planning especially important. We keep your reserves, financial statements, and disclosures accurate so your board can protect owners' investments.",
        },
        'miami': {
            'name': 'Miami',
            'state': 'Florida',
            'image_path': 'images/locations/cities/miami.jpg',
            'intro': "Miami's coastal condo towers face Florida's most stringent structural and reserve requirements. Dynamite Management helps Miami boards stay funded, compliant, and audit-ready.",
            'law': "Miami-area condominiums fall under Florida's Chapter 718 and the state's post-Surfside milestone inspection and Structural Integrity Reserve Study (SIRS) requirements, which mandate fully funded structural reserves. We handle the reserve accounting, financial reporting, and Form 1120-H tax preparation that keep your Miami association compliant.",
        },
        'chicago': {
            'name': 'Chicago',
            'state': 'Illinois',
            'image_path': 'images/locations/cities/chicago.jpg',
            'intro': "Chicago's high-rise condominiums and the City's own condominium ordinance add a layer of complexity for boards. Dynamite Management keeps Chicago associations' finances accurate and transparent.",
            'law': "Chicago condominiums are governed by the Illinois Condominium Property Act and the City of Chicago Condominium Ordinance, which give owners strong record-inspection rights and set disclosure standards. We provide the clear financial statements and recordkeeping that make compliance and owner requests straightforward.",
        },
        'portland': {
            'name': 'Portland',
            'state': 'Oregon',
            'image_path': 'images/locations/cities/portland.jpg',
            'intro': "Portland's condos and planned communities must fund reserves for the long term, and Dynamite Management helps Portland boards plan and report with confidence.",
            'law': "Portland associations follow Oregon's Planned Community Act (ORS Chapter 94) and Condominium Act (ORS Chapter 100), which require reserve studies and ongoing reserve funding. We keep your reserve schedules and financial statements accurate so your association meets Oregon's requirements.",
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

def hoa_taxes(request):
    """
    View for the HOA Taxes page
    """
    return render(request, 'core/hoa_taxes.html')

def wa_condo(request):
    """
    Landing page for the Washington self-managed condo postcard campaign.
    QR code on the postcard targets this URL (/wa-condo/).
    """
    return render(request, 'core/wa_condo.html')

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')

def terms_of_service(request):
    return render(request, 'core/terms_of_service.html')

@check_honeypot
def contact(request):
    """
    View for the contact page and form handling
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        
        if form.is_valid():
            try:
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
                
                # Log to console in development/debug environments
                print(f"Sending email with subject: {subject}")
                print(f"To: info@hoafiscal.com")
                
                # Send email
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
                # Log the error
                print(f"Error sending email: {str(e)}")
                messages.error(request, "Sorry, there was an error sending your message. Please try again later or contact us directly at (888) 575-0563.")
        else:
            # If form is invalid, display validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})