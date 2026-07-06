from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django import forms
from web.models import Fahrt, Zug


class UserRegistrationForm(UserCreationForm):
    # Auswahlfeld für die Rolle basierend auf den Django-Gruppen
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        label="Rolle"
    )

    # Initialisierung zur Anpassung der Feld-Styles (Trello-Task)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Sichtbare Konturen (border-gray-300) und horizontaler Innenabstand (pl-3) hinzufügen
            field.widget.attrs['class'] = (
                'w-full border border-gray-300 rounded-lg pl-3 pr-3 py-2 '
                'text-gray-900 bg-white shadow-sm focus:border-indigo-500 '
                'focus:ring-1 focus:ring-indigo-500 focus:outline-none text-sm'
            )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.save()

        # Den Benutzer der ausgewählten Gruppe (Rolle) zuweisen
        selected_group = self.cleaned_data.get('role')
        if selected_group:
            user.groups.add(selected_group)
        return user


class FahrtStartenForm(forms.ModelForm):
    # Wir überschreiben __init__, um das Queryset dynamisch und fehlerfrei zu laden
    def __init__(self, *source, **kwargs):
        super().__init__(*source, **kwargs)

        # 1. Holen Sie sich die IDs aller Züge, die JETZT gerade fahren (fahrt_ende ist leer)
        aktive_zug_ids = Fahrt.objects.filter(fahrt_ende__isnull=True).values_list('zug_id', flat=True)

        # 2. Zeige alle Züge, deren ID NICHT in dieser Liste der aktiven Züge steckt
        self.fields['zug'].queryset = Zug.objects.exclude(id__in=aktive_zug_ids)

    zug = forms.ModelChoiceField(
        queryset=Zug.objects.all(),  # Wird oben in __init__ sicher überschrieben
        empty_label="-- Bitte Zug auswählen --",
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 px-4 py-3 text-gray-900 focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-200 focus:outline-none transition appearance-none cursor-pointer text-sm'
        })
    )

    class Meta:
        model = Fahrt
        fields = ['zug']