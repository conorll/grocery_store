from django import forms
from .models_.store import Store

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

# Form for adding/editing store objects
class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['id', 'name', 'address', 'postcode', 'phone_number', 'opening_hours']