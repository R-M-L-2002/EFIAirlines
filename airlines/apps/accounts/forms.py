"""
forms para la app core
aca van los forms de registro, login y perfil de User
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.passengers.models import Passenger


class UserRegisterForm(UserCreationForm):
    """
    form personalizado para registrar Users
    extiende UserCreationForm y agrega campos extra
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        }),
        help_text='enter a valid email'
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name'
        }),
        label='Name'
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Lastname'
        }),
        label='Lastname'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # le metemos las clases css y placeholders copados
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'confirmar password'
        })
        
        # help texts explicativos para el User
        self.fields['username'].help_text = 'required, 150 chars max, only letters, digits and @/./+/-/_'
        self.fields['password1'].help_text = 'The password must have at least 8 characters.'

    def clean_email(self):
        """
        valida que el email no este ya registrado
        si esta, tira error para que no pase
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered')
        return email

    def save(self, commit=True):
        """
        guarda el User en la db
        si pasamos commit True, lo guarda, sino solo lo instancia
        """
        user = super().save(commit=False)
        # agregamos los campos extra
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """
    form de login con bootstrap
    solo cambia placeholders y clases, no toca logica
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or email',
            'autofocus': True
        }),
        label='User'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'password'
        }),
        label='password'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # sacamos el help text default que viene molesto :P
        self.fields['username'].help_text = None


class UserProfileForm(forms.ModelForm):
    """
    form para editar perfil
    solo cambia los campos basicos y valida email unico
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Name',
            'last_name': 'Lastname',
            'email': 'Email',
        }

    def clean_email(self):
        """
        valida que el email no este usado por otro user
        si ya esta, tira error
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This email is already registered by another User')
        return email


class PassengerForm(forms.ModelForm):
    """
    form para crear o editar info de un passenger
    """
    class Meta:
        model = Passenger
        fields = [
            'name', 'document_type', 'document', 
            'email', 'phone', 'birth_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name'
            }),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'document': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+54 11 1234-5678'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'name': 'Name',
            'document_type': 'Document Type',
            'document': 'Document number',
            'email': 'Email',
            'phone': 'Phone',
            'birth_date': 'Birthdate',
        }

    def clean_document(self):
        """
        valida que el documento no este repetido
        si ya existe, tira error
        """
        document = self.cleaned_data.get('document')
        if Passenger.objects.filter(document=document).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError('This document is already registered')
        return document
