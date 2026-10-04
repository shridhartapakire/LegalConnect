from django import forms

from .models import VerificationDocument


class VerificationDocumentUploadForm(forms.ModelForm):
    class Meta:
        model = VerificationDocument
        fields = ("evidence_type", "file")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["evidence_type"].queryset = self.fields["evidence_type"].queryset.filter(is_active=True)

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        from .models import validate_verification_file

        validate_verification_file(uploaded_file)
        return uploaded_file


class VerificationReviewForm(forms.Form):
    status = forms.ChoiceField(choices=[])
    comment = forms.CharField(widget=forms.Textarea, required=False, max_length=2_000)
    expires_at = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, application, *args, **kwargs):
        self.application = application
        super().__init__(*args, **kwargs)
        allowed = {
            application.Status.SUBMITTED: (application.Status.UNDER_REVIEW, application.Status.NEEDS_MORE_INFORMATION, application.Status.VERIFIED, application.Status.REJECTED),
            application.Status.UNDER_REVIEW: (application.Status.NEEDS_MORE_INFORMATION, application.Status.VERIFIED, application.Status.REJECTED),
            application.Status.VERIFIED: (application.Status.SUSPENDED, application.Status.REVOKED),
            application.Status.SUSPENDED: (application.Status.VERIFIED, application.Status.REVOKED),
        }
        self.fields["status"].choices = [(choice, application.Status(choice).label) for choice in allowed.get(application.status, ())]

    def clean(self):
        cleaned_data = super().clean()
        requires_comment = {"NEEDS_MORE_INFORMATION", "REJECTED", "SUSPENDED", "REVOKED"}
        if cleaned_data.get("status") in requires_comment and not cleaned_data.get("comment", "").strip():
            self.add_error("comment", "A reason or comment is required for this decision.")
        return cleaned_data
