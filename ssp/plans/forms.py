from django import forms

from .models import Detail


class DetailForm(forms.ModelForm):
    status = forms.ChoiceField(choices=Detail.STATUS_CHOICES_FORM)

    class Meta:
        model = Detail
        fields = ["stauts", "text"]
