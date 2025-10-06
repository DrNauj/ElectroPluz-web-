from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(forms.Form):
    nombre_usuario = forms.CharField(
        label='Nombre de Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su nombre de usuario',
            'id': 'id_nombre_usuario'
        })
    )
    contrasena = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña',
            'id': 'id_contrasena'
        })
    )
    user_type = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'userType'
        })
    )
    remember = forms.BooleanField(
        required=False,
        initial=False,
        label='Recordarme',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'remember'
        })
    )

class RegisterForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su nombre completo'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su correo electrónico'
        })
    )
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Elija un nombre de usuario'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme su contraseña'
        })
    )
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden')