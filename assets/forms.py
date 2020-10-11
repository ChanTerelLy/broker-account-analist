from django import forms
from .models import Account
class UploadFile(forms.Form):
    file = forms.FileField(label='Загрузите файл')

class UploadTransferFile(forms.Form):
    file = forms.FileField(label='Загрузите файл')
    account_income = forms.ModelMultipleChoiceField(queryset=Account.objects.none())
    account_charge = forms.ModelMultipleChoiceField(queryset=Account.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(UploadTransferFile, self).__init__(*args, **kwargs)
        if user:
            self.fields['account_income'].queryset = Account.objects.filter(user_id=user.id)
            self.fields['account_charge'].queryset = Account.objects.filter(user_id=user.id)

