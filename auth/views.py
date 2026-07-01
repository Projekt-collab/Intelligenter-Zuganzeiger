from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from web.models import Zug, Fahrt
from django.utils import timezone
from .forms import UserRegistrationForm, FahrtStartenForm
from django.core.exceptions import PermissionDenied


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

    return render(request, 'register.html', {'form': form})


# 2. Dashboard mit Rollenprüfung
@login_required
def dashboard_view(request):
    aktuelle_fahrt = Fahrt.objects.filter(
        lokfuehrer=request.user,
        fahrt_ende__isnull=True
    ).first()
    
    if aktuelle_fahrt:
        return redirect('lokfuehrer')

    if request.method == 'POST':
        form = FahrtStartenForm(request.POST)
        if form.is_valid():
            # commit=False sorgt dafür, dass die Fahrt noch nicht in die DB gespeichert wird
            fahrt = form.save(commit=False)
            fahrt.lokfuehrer = request.user
            fahrt.fahrt_beginn = timezone.now()
            fahrt.save()

            return redirect('lokfuehrer')
    else:
        form = FahrtStartenForm()

    return render(request, 'dashboard.html', {'form': form})



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