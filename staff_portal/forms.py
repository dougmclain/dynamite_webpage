from django import forms
from django.contrib.auth.forms import AuthenticationForm
from tinymce.widgets import TinyMCE
from blog.models import BlogPost, Category, Tag


class StaffLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Username",
            "autofocus": True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password",
        })
    )


class BlogPostForm(forms.ModelForm):
    content = forms.CharField(widget=TinyMCE())
    new_category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Or create new category...",
        }),
    )
    new_tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Comma-separated new tags...",
        }),
    )

    class Meta:
        model = BlogPost
        fields = [
            "title", "slug", "content", "excerpt", "featured_image",
            "category", "tags", "status", "published_at",
            "meta_description", "meta_keywords",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Post title"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "auto-generated-from-title"}),
            "excerpt": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Brief excerpt (auto-generated if blank)"}),
            "featured_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-select", "size": 5}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "published_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "meta_description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "SEO meta description (160 chars max)"}),
            "meta_keywords": forms.TextInput(attrs={"class": "form-control", "placeholder": "keyword1, keyword2, keyword3"}),
        }
        labels = {
            "published_at": "Publish date",
        }
        help_texts = {
            "published_at": "When the post was actually written. Leave blank to auto-set to now when first published.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["published_at"].required = False
        # The HTML datetime-local input needs the right input format
        self.fields["published_at"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle new category creation
        new_cat = self.cleaned_data.get("new_category", "").strip()
        if new_cat:
            category, _ = Category.objects.get_or_create(name=new_cat)
            instance.category = category

        if commit:
            instance.save()
            self.save_m2m()

            # Handle new tags after save (needs pk for m2m)
            new_tags_str = self.cleaned_data.get("new_tags", "").strip()
            if new_tags_str:
                for tag_name in new_tags_str.split(","):
                    tag_name = tag_name.strip()
                    if tag_name:
                        tag, _ = Tag.objects.get_or_create(name=tag_name)
                        instance.tags.add(tag)

        return instance


class AIGenerationForm(forms.Form):
    topic = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "e.g., Reserve Fund Best Practices for HOAs",
        }),
    )
    tone = forms.ChoiceField(
        choices=[
            ("professional", "Professional"),
            ("conversational", "Conversational"),
            ("educational", "Educational"),
            ("authoritative", "Authoritative"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    length = forms.ChoiceField(
        choices=[
            ("500", "Short (~500 words)"),
            ("1000", "Medium (~1000 words)"),
            ("1500", "Long (~1500 words)"),
        ],
        initial="1000",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    audience = forms.ChoiceField(
        choices=[
            ("hoa_board", "HOA Board Members"),
            ("property_managers", "Property Managers"),
            ("condo_owners", "Condo Owners"),
            ("general", "General Audience"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
