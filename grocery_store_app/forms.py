from django import forms

class PostcodeForm(forms.Form):
    postcode = forms.CharField(
        label="Enter your postcode",
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 2000'
        })
    )