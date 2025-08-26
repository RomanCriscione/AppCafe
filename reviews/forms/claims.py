# reviews/forms/claims.py
from django import forms
from reviews.models.claims import ClaimMethod, ClaimRequest


class ClaimStartForm(forms.ModelForm):
    class Meta:
        model = ClaimRequest
        fields = ["method", "notes_user"]

    def __init__(self, *args, cafe=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el café no tiene email, ocultamos EMAIL_DOMAIN
        choices = []
        if getattr(cafe, "email", None):
            choices.append((ClaimMethod.EMAIL_DOMAIN, ClaimMethod.EMAIL_DOMAIN.label))
        choices.extend([
            (ClaimMethod.PHOTO_CODE, ClaimMethod.PHOTO_CODE.label),
            (ClaimMethod.PHONE, ClaimMethod.PHONE.label),
        ])
        self.fields["method"].widget = forms.RadioSelect(choices=choices)
        self.fields["notes_user"].widget = forms.Textarea(attrs={"rows": 3, "placeholder": "Contanos cómo podemos verificar rápido."})


class ClaimVerifyEmailForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code"}),
        label="Código de verificación",
    )


class ClaimEvidenceForm(forms.Form):
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        required=True,
        help_text="Subí 1–4 archivos: ticket del día, foto del mostrador con el código, etc.",
    )

    def clean_files(self):
        files = self.files.getlist("files")
        if not 1 <= len(files) <= 4:
            raise forms.ValidationError("Subí entre 1 y 4 archivos.")
        return files
