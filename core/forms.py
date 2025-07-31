from django import forms
from .models import DemandeAcces

class DemandeAccesForm(forms.ModelForm):
    class Meta:
        model = DemandeAcces
        fields = ['nom_complet', 'email', 'role_souhaite', 'message']
