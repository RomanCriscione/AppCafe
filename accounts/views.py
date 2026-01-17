# accounts/views.py
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect

from .forms import CustomUserCreationForm, CustomUserChangeForm



# ---- Registro de usuario común
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('account_login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


# ---- Editar avatar / perfil básico
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


# ---- Perfil simple
@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


# ---- Convertir cuenta en "dueño" (owner)
@login_required
def register_owner(request):
    if request.method == "POST":
        # Validación extra, por el momento no
        # form = OwnerSignupForm(request.POST, instance=request.user)
        # if form.is_valid():
        #     user = form.save(commit=False)
        #     user.is_owner = True
        #     user.save(update_fields=["is_owner"])
        # else:
        #     return render(request, "accounts/register_owner.html", {"form": form})

        # Sin formulario: marcar como dueño directamente
        user = request.user
        if not user.is_owner:
            user.is_owner = True
            user.save(update_fields=["is_owner"])

        messages.success(request, "¡Listo! Tu cuenta ahora es de dueño de cafetería.")
        next_url = request.GET.get("next")
        return redirect(next_url or reverse("reviews:owner_dashboard"))

    # GET
    # return render(request, "accounts/register_owner.html", {"form": OwnerSignupForm(instance=request.user)})
    return render(request, "accounts/register_owner.html")


@login_required
def my_account(request):
    return render(request, "accounts/my_account.html")