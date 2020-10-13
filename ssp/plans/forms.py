from django import forms

from ssp.controls.models import Control
from .models import Plan


class NewPlanForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewPlanForm, self).__init__(*args, **kwargs)
        if "initial" in kwargs:
            self.fields["root_control"].queryset = Control.objects.filter(
                parent__isnull=True
            )

    class Meta:
        model = Plan
        fields = ["title", "description", "root_control"]
