from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm, CustomUserChangeForm

# Vista de registro de usuario
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')  # Asegurate de que 'login' esté en tus urls
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


# Vista para editar avatar y otros datos del usuario
@login_required
def edit_avatar(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'accounts/edit_avatar.html', {'form': form})



# Vista de perfil del usuario
@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

from .forms import OwnerSignupForm

def register_owner(request):
    if request.method == 'POST':
        form = OwnerSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            return redirect('owner_dashboard')  # Asegúrate de tener esta URL creada
    else:
        form = OwnerSignupForm()
    return render(request, 'accounts/register_owner.html', {'form': form})
