from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import UserProfile, Contact

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, label="Username")
    email = forms.EmailField(required=True, label="Email Address")
    phone = forms.CharField(
        max_length=15,
        required=True,
        label="Phone Number",
        validators=[RegexValidator(
            r'^\+977\d{9,10}$',
            'Enter a valid Nepal phone number starting with +977 followed by 9-10 digits (e.g., +9779817158500).'
        )]
    )
    address = forms.CharField(widget=forms.Textarea, required=True, label="Home Address")
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm Password")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'class': 'form-control border-danger'}),
            'phone': forms.TextInput(attrs={'class': 'form-control border-danger', 'placeholder': 'Phone number'}),
        }

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['message', 'phone']:
                field.widget.attrs.update({'class': 'form-control border-danger'})