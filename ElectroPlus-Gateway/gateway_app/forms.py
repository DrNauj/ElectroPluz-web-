from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
# Importamos modelos necesarios. Asumo que Profile y Order están definidos en models.py
# para que los ModelForm funcionen correctamente, aunque la lógica del Gateway use microservicios.
from .models import Profile, Order 


# --- 1. Formulario de Inicio de Sesión (Custom) ---

class CustomLoginForm(AuthenticationForm):
    """
    Formulario de inicio de sesión que extiende el de Django.
    """
    username = forms.CharField(
        label=_("Nombre de Usuario o Email"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su nombre de usuario o email'),
            'autocomplete': 'username' 
        })
    )
    
    password = forms.CharField(
        label=_("Contraseña"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su contraseña'),
            'autocomplete': 'current-password'
        })
    )


# --- 2. Formulario de Registro ---

# Heredamos de UserCreationForm para aprovechar su lógica de validación de contraseñas
class RegisterForm(UserCreationForm):
    """
    Formulario de registro para nuevos usuarios.
    Añade campos para First Name y Last Name para ser más amigable.
    """
    # Sobrescribimos username y password para añadir clases CSS
    username = forms.CharField(
        label=_("Nombre de Usuario"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Usuario único')})
    )
    
    email = forms.EmailField(
        label=_("Correo Electrónico"),
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('ejemplo@dominio.com')})
    )
    
    first_name = forms.CharField(
        label=_("Nombre"),
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Su nombre')})
    )
    
    last_name = forms.CharField(
        label=_("Apellido"),
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Su apellido')})
    )
    
    # UserCreationForm ya incluye password1 y password2, solo ajustamos los widgets
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    # El campo de email y los campos de nombre/apellido se añaden por defecto
    class Meta(UserCreationForm.Meta):
        # Mantenemos 'username', 'password' y 'password2' de la clase base
        fields = ('username', 'email', 'first_name', 'last_name') 


# --- 3. Formulario de Perfil (ProfileForm) ---

class ProfileForm(forms.ModelForm):
    """
    Formulario para editar la información extendida del perfil de cliente.
    """
    class Meta:
        model = Profile
        fields = ['phone', 'address', 'city', 'state', 'zip_code', 'country', 'avatar']
        
        # Widgets para aplicar clases de estilo
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Número de Teléfono')}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Dirección completa')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ciudad')}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Estado/Provincia')}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Código Postal')}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('País')}),
            # Se usa FileInput para la carga de imágenes
            'avatar': forms.FileInput(attrs={'class': 'form-control'})
        }

# --- 4. Formulario de Checkout/Envío (CheckoutForm) ---

class CheckoutForm(forms.ModelForm):
    """Formulario para la información de envío y contacto de una Orden."""
    class Meta:
        model = Order
        # Solo usamos los campos de envío y contacto, no los totales ni status.
        fields = [
            'shipping_name', 'shipping_address', 'shipping_city', 'shipping_state', 
            'shipping_zip', 'shipping_country', 'email', 'phone'
        ]
        widgets = {
            'shipping_name': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_state': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_zip': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_country': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
