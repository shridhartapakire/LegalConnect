from django import forms

from apps.accounts.models import Locality, PracticeArea
from .models import ConsultationRequest


class ConsultationRequestForm(forms.ModelForm):
    class Meta:
        model = ConsultationRequest
        fields = ("subject", "description", "practice_area", "preferred_mode", "preferred_locality")
        widgets = {"description": forms.Textarea(attrs={"rows": 7})}

    def __init__(self, advocate, *args, **kwargs):
        self.advocate = advocate
        super().__init__(*args, **kwargs)
        self.fields["practice_area"].queryset = advocate.practice_areas.filter(is_active=True)
        self.fields["preferred_locality"].queryset = advocate.service_areas.filter(is_active=True)


class DeclineForm(forms.Form):
    reason = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={"rows": 4}))
