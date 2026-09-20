from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class SignupForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(min_length=12, widget=forms.PasswordInput)

class ContributionForm(forms.Form):
    kind = forms.ChoiceField(choices=[("new_model", "New model"), ("edit_model", "Edit model")])
    title = forms.CharField(max_length=160)
    details = forms.CharField(max_length=4000, widget=forms.Textarea)
    source_url = forms.URLField(max_length=600, required=False)
    translation_only = forms.BooleanField(required=False)
    def clean(self):
        data = super().clean()
        if not data.get("source_url") and not data.get("translation_only"):
            self.add_error("source_url", "A source is required except for a translation-only change.")
        return data
