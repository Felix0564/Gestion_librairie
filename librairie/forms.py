from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Etudiant

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    contact = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "contact", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class LivreSearchForm(forms.Form):
    query = forms.CharField(label='Rechercher', max_length=100, required=False)

class EmpruntForm(forms.Form):
    date_retour_prevue = forms.DateField(
        label="Date de retour prévue",
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now().date() + timezone.timedelta(days=14)
    )

    def clean_date_retour_prevue(self):
        date_retour = self.cleaned_data['date_retour_prevue']
        if date_retour <= timezone.now().date():
            raise forms.ValidationError("La date de retour doit être dans le futur.")
        return date_retour

class EmpruntConfirmationForm(forms.Form):
    confirmer = forms.BooleanField(required=True, label="Je confirme l'emprunt avec ces dates")



