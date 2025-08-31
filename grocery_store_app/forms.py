from django import forms
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