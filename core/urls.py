from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    
    # State location pages
    path('locations/<str:location_name>/', views.location_detail, {'location_type': 'state'}, name='state_detail'),
    
    # City location pages
    path('locations/<str:state_name>/<str:location_name>/', views.location_detail, {'location_type': 'city'}, name='city_detail'),
    
    # Financial Management page
    path('condo-financial-management/', views.financial_management, name='financial_management'),
    
    # About page
    path('about/', views.about, name='about'),
    
    # Blog page
    path('blog/', views.blog, name='blog'),
    
    # Contact page
    path('contact/', views.contact, name='contact'),
]