from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models.store import Store

# Form for user to input postcode to find closest store
class PostcodeForm(forms.Form):
    postcode = forms.CharField(
        label="Enter your postcode",
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 2000'
        })
    )

# Custom user registration form extending Django's UserCreationForm
class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name and not first_name.isalpha():
            raise forms.ValidationError("First name must contain only alphabetic characters.")
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name and not last_name.isalpha():
            raise forms.ValidationError("Last name must contain only alphabetic characters.")
        return last_name

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

