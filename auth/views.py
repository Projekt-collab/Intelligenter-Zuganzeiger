from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm


# 1. Registrierung
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatischer Login nach Registrierung
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


# 2. Dashboard mit Rollenprüfung
@login_required
def dashboard_view(request):
    # Prüfen, ob der Benutzer in bestimmten Gruppen existiert
    is_admin = request.user.groups.filter(name='Admin').exists()
    is_manager = request.user.groups.filter(name='Manager').exists()

    context = {
        'is_admin': is_admin,
        'is_manager': is_manager,
    }

    return render(request, 'users/dashboard.html', context)

from django.core.exceptions import PermissionDenied

def group_required(group_names=[]):
    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            user_groups = request.user.groups.values_list('name', flat=True)
            # Prüfen, ob der User in einer der erlaubten Gruppen ist (oder Superuser)
            if any(group in group_names for group in user_groups) or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied # Gibt einen HTTP 403 Fehler aus
        return wrap
    return decorator

# Beispiel für die Verwendung:
@login_required
@group_required(group_names=['Admin', 'Manager'])
def management_only_view(request):
    return render(request, 'management.html')