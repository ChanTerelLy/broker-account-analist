from django import forms

class DealsUploadForm(forms.Form):
    file = forms.FileField(label='Upload deals file')