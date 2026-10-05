from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Customer, Review


class CreateUserForm(UserCreationForm):
    """Enhanced user registration form"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email


class CustomerProfileForm(forms.ModelForm):
    """Customer profile update form"""
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    class Meta:
        model = Customer
        fields = ['phone', 'address', 'city', 'region', 'profile_image', 'is_farmer']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number (e.g., +256...)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Full Address',
                'rows': 3
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City/Town'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Region/District'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'is_farmer': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class ReviewForm(forms.ModelForm):
    """Product review form"""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-control'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your review...',
                'rows': 4
            }),
        }


class CheckoutForm(forms.Form):
    """Checkout form for shipping information"""
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    phone = forms.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\\+?[0-9 ()-]{9,20}
            'class': 'form-control',
            'placeholder': 'Phone Number'
        })
    )
    address = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Street Address'
        })
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City/Town'
        })
    )
    region = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Region/District'
        })
    )
    country = forms.CharField(
        max_length=100,
        initial='Uganda',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country'
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal Code (Optional)'
        })
    )
    delivery_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Delivery Instructions (Optional)',
            'rows': 2
        })
    )
, 'Enter a valid phone number.')],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number'
        })
    )
    address = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Street Address'
        })
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City/Town'
        })
    )
    region = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Region/District'
        })
    )
    country = forms.CharField(
        max_length=100,
        initial='Uganda',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country'
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal Code (Optional)'
        })
    )
    delivery_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Delivery Instructions (Optional)',
            'rows': 2
        })
    )
