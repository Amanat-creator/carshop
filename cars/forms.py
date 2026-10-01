from django import forms


INPUT_STYLE = 'width:100%; padding:12px; border:1px solid #ddd; border-radius:8px; font-size:14px; box-sizing:border-box;'


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label='Ваше имя',
        widget=forms.TextInput(attrs={'style': INPUT_STYLE, 'placeholder': 'Иван Иванов'})
    )
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        widget=forms.TextInput(attrs={'style': INPUT_STYLE, 'placeholder': '+7 (999) 123-45-67'})
    )
    email = forms.EmailField(
        required=False,
        label='Email (необязательно)',
        widget=forms.EmailInput(attrs={'style': INPUT_STYLE, 'placeholder': 'you@example.com'})
    )
    message = forms.CharField(
        label='Сообщение',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'style': INPUT_STYLE,
            'placeholder': 'Здравствуйте! Интересует этот автомобиль...'
        })
    )


from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'style': INPUT_STYLE, 'placeholder': 'you@example.com'})
    )
    first_name = forms.CharField(
        required=False,
        max_length=50,
        label='Имя',
        widget=forms.TextInput(attrs={'style': INPUT_STYLE, 'placeholder': 'Иван'})
    )
    last_name = forms.CharField(
        required=False,
        max_length=50,
        label='Фамилия',
        widget=forms.TextInput(attrs={'style': INPUT_STYLE, 'placeholder': 'Иванов'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Применяем стили ко всем полям
        for field_name, field in self.fields.items():
            field.widget.attrs['style'] = INPUT_STYLE
        self.fields['username'].widget.attrs['placeholder'] = 'ivan_ivanov'
        self.fields['username'].label = 'Логин'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повторите пароль'