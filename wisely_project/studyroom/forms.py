from django import forms
from studyroom.models import Session

__author__ = 'tmehta'


class CreateSessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['name', 'password', 'public', 'audio', 'video', 'code']
        widgets = {
            'password': forms.CharField(widget=forms.PasswordInput, required=False)
        }
