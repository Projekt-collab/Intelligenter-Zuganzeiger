from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm


class UserRegistrationForm(UserCreationForm):
    # Auswahlfeld für die Rolle basierend auf den Django-Gruppen
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        label="Rolle"
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