from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class CustomRegistrationForm(UserCreationForm):
    # We subclass the built-in form so we don't have to write the password-hashing logic
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email') # Adding email just to make it a real app

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This injects our dark-theme CSS classes into the HTML inputs automatically
        for field in self.fields.values():
            field.widget.attrs['class'] = 'custom-input'
            field.widget.attrs['placeholder'] = field.label

class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'custom-input'
            field.widget.attrs['placeholder'] = field.label