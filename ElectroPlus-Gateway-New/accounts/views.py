from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'storefront:product_list')
            return JsonResponse({
                'success': True,
                'redirect_url': next_url,
                'message': f'Bienvenido, {user.get_full_name() or user.username}!'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({
                'success': True,
                'redirect_url': 'storefront:product_list',
                'message': '¡Registro exitoso! Bienvenido a ElectroPlus'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, '¡Hasta pronto!')
    return redirect('storefront:product_list')
