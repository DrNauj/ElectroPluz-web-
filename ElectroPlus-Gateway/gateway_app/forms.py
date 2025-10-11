from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import Profile, Order # Aseguramos que los modelos estén disponibles

# --- 1. Formulario de Inicio de Sesión (Recomendado) ---

# Se recomienda heredar de AuthenticationForm para aprovechar la validación
# de usuario y contraseña de Django.
class CustomLoginForm(AuthenticationForm):
    """
    Formulario de inicio de sesión que extiende el de Django para añadir 
    clases CSS y el campo "Recordarme".
    """
    # Renombrar campos para consistencia, usando los nombres estándar de Django: 'username' y 'password'.
    # AuthenticationForm ya define estos campos, solo ajustamos los widgets.
    
    # Sobrescribimos el widget del campo 'username' (que AuthenticationForm llama 'username')
    username = forms.CharField(
        label=_("Nombre de Usuario"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su nombre de usuario'),
            'autocomplete': 'username' # Ayuda a los navegadores a recordar
        })
    )
    
    # Sobrescribimos el widget del campo 'password'
    password = forms.CharField(
        label=_("Contraseña"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su contraseña'),
            'autocomplete': 'current-password'
        })
    )
    
    # Añadimos el campo 'remember' (opcional, para gestionar la sesión en la vista)
    remember = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Recordarme'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    # El campo user_type se eliminó ya que no es estándar para el login.

# --- 2. Formulario de Registro (Mejorado para User model) ---

class RegisterForm(forms.Form):
    """
    Formulario de registro personalizado.
    Se recomienda usar UserCreationForm o un formulario que se alinee mejor con el modelo User.
    Aquí se ajustaron los nombres de campo para mapear mejor.
    """
    first_name = forms.CharField(
        label=_("Nombre"),
        max_length=150, # Max length de First Name en User
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su nombre')
        })
    )
    
    # Se añade Last Name, aunque es opcional en el modelo User
    last_name = forms.CharField(
        label=_("Apellido"),
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su apellido (opcional)')
        })
    )
    
    email = forms.EmailField(
        label=_("Correo Electrónico"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su correo electrónico')
        })
    )
    
    username = forms.CharField(
        label=_("Nombre de Usuario"),
        max_length=150, # Max length de Username en User
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Elija un nombre de usuario')
        })
    )
    
    password = forms.CharField( # Se renombra a 'password' para mayor claridad interna
        label=_("Contraseña"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su contraseña'),
            'autocomplete': 'new-password'
        })
    )
    
    password_confirm = forms.CharField( # Se renombra a 'password_confirm'
        label=_("Confirmar Contraseña"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirme su contraseña'),
            'autocomplete': 'new-password'
        })
    )
    
    terms = forms.BooleanField(
        required=True,
        label=_('Acepto los términos y condiciones'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm') # Usamos el nuevo nombre

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(_('Las contraseñas no coinciden'))
        
        return cleaned_data # IMPORTANTE: Siempre retornar cleaned_data

# --- 3. Formulario de Perfil (ModelForm) ---

class ProfileForm(forms.ModelForm):
    """Formulario para actualizar la información de perfil del usuario."""
    class Meta:
        model = Profile
        fields = ['phone', 'address', 'city', 'state', 'zip_code', 'country', 'avatar']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'})
        }

# --- 4. Formulario de Checkout/Envío (ModelForm) ---

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
            'phone': forms.TextInput(attrs={'class': 'form-control'})
        }
