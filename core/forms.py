from django import forms
from honeypot.decorators import check_honeypot

class ContactForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    comments = forms.CharField(widget=forms.Textarea, required=True)

    
    # No need for custom clean method as Captcha field handles validation automatically