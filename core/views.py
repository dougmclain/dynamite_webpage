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
            'law': "California community associations are governed by the Davis-Stirling Common Interest Development Act (Civil Code §4000 et seq.), which sets detailed rules for annual budgets, reserve funding, owner disclosures, and assessment collection. Boards must distribute an annual budget report each year — including a pro forma operating budget and a reserve funding disclosure — and most associations must complete a full reserve study at least every three years, reviewing it annually. We keep your financial statements, reserve reporting, and required disclosures accurate and on schedule so your California board stays compliant.",
        },
        'florida': {
            'name': 'Florida',
            'image_path': 'images/locations/florida.jpg',
            'intro': "Florida's condominium and HOA communities — especially along the coast — face the nation's most demanding financial and structural-reserve requirements. Dynamite Management helps Florida boards stay funded, compliant, and audit-ready.",
            'law': "Florida condominiums fall under Chapter 718 and HOAs under Chapter 720 of the Florida Statutes. Following the 2021 Surfside collapse, the state now requires milestone inspections and Structural Integrity Reserve Studies (SIRS) for condominium and cooperative buildings three or more habitable stories tall, and reserves for the SIRS structural components generally can no longer be waived. Under 2025's HB 913, boards gained more funding flexibility — including special assessments, loans, or lines of credit, and a limited pause after a milestone inspection — making accurate reserve reporting, financial statements, and Form 1120-H tax preparation more important than ever.",
        },
        'georgia': {
            'name': 'Georgia',
            'image_path': 'images/locations/georgia.jpg',
            'intro': "Georgia's fast-growing metro and suburban communities depend on sound association finances to protect property values. Dynamite Management provides Georgia HOA and condo boards with professional accounting and fraud-protection controls.",
            'law': "Georgia associations are typically governed by the Georgia Property Owners' Association Act (O.C.G.A. §44-3-220 et seq.) or the Georgia Condominium Act (O.C.G.A. §44-3-70 et seq.), depending on how the community was organized. A major 2026 reform — the Georgia Property Owners' Bill of Rights Act (SB 406) — adds Secretary of State registration, a 10-year financial-records retention rule, and new assessment and payment-application requirements, with most provisions taking effect January 1, 2027. Sound bookkeeping and long-term financial records will be essential for compliance, and that is exactly what we provide.",
        },
        'hawaii': {
            'name': 'Hawaii',
            'image_path': 'images/locations/hawaii.jpg',
            'intro': "Hawaii's condominium associations manage high-value property in a unique island market, where careful financial stewardship is essential. Dynamite Management delivers islands-wide associations dependable accounting and reserve oversight.",
            'law': "Hawaii condominiums are governed by HRS Chapter 514B (the Condominium Property Act), with planned community associations covered under HRS Chapter 421J. Chapter 514B requires condominium boards to base their budgets on a reserve study and to fund replacement reserves at statutory levels, with the study reviewed at least every three years; Chapter 421J communities have fewer explicit reserve mandates but face the same long-term risks. We manage your financial statements, reserve reporting, and tax filings so your Hawaii board can meet those obligations with confidence.",
        },
        'illinois': {
            'name': 'Illinois',
            'image_path': 'images/locations/illinois.jpg',
            'intro': "From Chicago high-rises to suburban townhome communities, Illinois associations operate under detailed condominium and common-interest statutes. Dynamite Management keeps Illinois boards' books accurate and their owners informed.",
            'law': "Illinois condominiums are governed by the Condominium Property Act (765 ILCS 605), and many non-condominium communities by the Common Interest Community Association Act (765 ILCS 160). Both require boards to budget for reasonable reserves for capital expenditures and deferred maintenance and to disclose reserve allocations to owners, though Illinois does not mandate reserve studies on a fixed schedule. We provide the transparent financial statements and recordkeeping that keep your association compliant and owner requests easy to answer.",
        },
        'new-york': {
            'name': 'New York',
            'image_path': 'images/locations/new-york.jpg',
            'intro': "New York's condos and co-ops carry significant financial responsibility in one of the country's most demanding real-estate markets. Dynamite Management supports New York boards with rigorous accounting and reserve oversight.",
            'law': "New York condominiums are formed under the Condominium Act (Article 9-B of the Real Property Law), while cooperatives are organized as corporations governed largely by the Business Corporation Law and their proprietary leases. The two structures carry different financial, reporting, and tax considerations — including whether a condominium files Form 1120-H. We handle the accounting, reserve tracking, and association tax preparation that keep your New York community financially sound.",
        },
        'oregon': {
            'name': 'Oregon',
            'image_path': 'images/locations/oregon.jpg',
            'intro': "Oregon's planned communities and condominiums are required to plan ahead financially — and Dynamite Management helps Oregon boards do exactly that with dependable accounting and reserve reporting.",
            'law': "Oregon associations are governed by the Oregon Planned Community Act (ORS Chapter 94) and the Oregon Condominium Act (ORS Chapter 100), which require a reserve account, a reserve study, and a maintenance plan for most communities (ORS 94.595 and ORS 100.175). Boards must review or update the reserve study and fund the reserve account, with only limited owner-approved opportunities to skip funding in a given year. We keep your reserve schedules, financial statements, and filings accurate so your association meets Oregon's requirements.",
        },
        'texas': {
            'name': 'Texas',
            'image_path': 'images/locations/texas.jpg',
            'intro': "Texas's fast-growing HOA and condo communities need finances that scale with them. Dynamite Management gives Texas boards professional accounting, collections support, and fraud protection.",
            'law': "Texas HOAs are governed by the Texas Residential Property Owners Protection Act (Chapter 209 of the Property Code), and condominiums by the Texas Uniform Condominium Act (Chapter 82, for declarations recorded on or after January 1, 1994). These statutes set rules for assessments, collections, records retention, and owner notices, but Texas does not mandate reserve studies — making proactive reserve reporting and clear financial statements a best practice. We also handle Form 1120-H tax preparation, a common need for both HOAs and condos.",
        },
        'washington': {
            'name': 'Washington',
            'image_path': 'images/locations/washington.jpg',
            'intro': "Washington associations are in the middle of a major legal transition, and Dynamite Management helps Washington boards — especially self-managed condos — stay compliant and financially healthy.",
            'law': "Washington's common-interest communities are increasingly governed by the Washington Uniform Common Interest Ownership Act (WUCIOA, RCW 64.90), which sets requirements for budgets, reserve studies, and reserve funding. Under 2024's \"WUCIOA for All\" law (SB 5796), WUCIOA will apply to essentially all condominiums and HOAs regardless of formation date starting January 1, 2028, repealing the older Condominium Act (RCW 64.34) and Homeowners' Associations Act (RCW 64.38) — and some provisions, including reserve studies and budget rules, already apply retroactively. We keep your reserve studies, financial statements, and disclosures aligned with WUCIOA so your board stays ahead of the transition.",
        },
    }

    cities = {
        'san-francisco': {
            'name': 'San Francisco',
            'state': 'California',
            'image_path': 'images/locations/cities/san-francisco.jpg',
            'intro': "San Francisco's dense condominium market and high property values make professional association finances essential. Dynamite Management serves San Francisco condo and HOA boards with dedicated accounting and oversight.",
            'law': "San Francisco associations operate under California's Davis-Stirling Common Interest Development Act (Civil Code §4000 et seq.), with its detailed budget, reserve-funding, and annual disclosure requirements; most associations complete a full reserve study at least every three years. There is no separate San Francisco condo ordinance, so state law controls — and the city's older, high-value buildings make reserve planning especially important. We keep your reserves, financial statements, and disclosures accurate so your board can protect owners' investments.",
        },
        'miami': {
            'name': 'Miami',
            'state': 'Florida',
            'image_path': 'images/locations/cities/miami.jpg',
            'intro': "Miami's coastal condo towers face Florida's most stringent structural and reserve requirements. Dynamite Management helps Miami boards stay funded, compliant, and audit-ready.",
            'law': "Miami-area condominiums fall under Florida's Chapter 718 and the state's post-Surfside milestone inspection and Structural Integrity Reserve Study (SIRS) requirements, which apply to buildings three or more habitable stories tall. Reserves for the SIRS structural components generally cannot be waived, though 2025's HB 913 added funding flexibility such as special assessments, loans, and lines of credit, plus a limited post-inspection pause. Miami's older coastal high-rises make accurate reserve reporting, financial statements, and Form 1120-H tax preparation especially important.",
        },
        'chicago': {
            'name': 'Chicago',
            'state': 'Illinois',
            'image_path': 'images/locations/cities/chicago.jpg',
            'intro': "Chicago's high-rise condominiums and the City's own condominium ordinance add a layer of complexity for boards. Dynamite Management keeps Chicago associations' finances accurate and transparent.",
            'law': "Chicago condominiums are governed by the Illinois Condominium Property Act (765 ILCS 605) and the City of Chicago Condominium Ordinance (Municipal Code Chapter 13-72), which gives owners strong record-inspection rights — including access to financial books and records for the current and 10 preceding fiscal years. Boards must also retain key disclosure documents for several years. We provide the organized financial statements and recordkeeping that make compliance and owner requests straightforward.",
        },
        'portland': {
            'name': 'Portland',
            'state': 'Oregon',
            'image_path': 'images/locations/cities/portland.jpg',
            'intro': "Portland's condos and planned communities must fund reserves for the long term, and Dynamite Management helps Portland boards plan and report with confidence.",
            'law': "Portland associations follow Oregon's Planned Community Act (ORS Chapter 94) and Condominium Act (ORS Chapter 100), which require a reserve account, a reserve study, and a maintenance plan for most communities (ORS 94.595 and ORS 100.175). Boards must review or update the study and fund reserves, with only limited owner-approved exceptions. There is no separate Portland condo ordinance, so ongoing reserve reporting and financial statements are what keep boards aligned with state law.",
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