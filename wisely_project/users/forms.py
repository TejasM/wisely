from django import forms
from django.forms.extras.widgets import SelectDateWidget

from models import UserProfile


class UserProfileForm(forms.ModelForm):
    picture = forms.ImageField(help_text="Please select a profile image to upload.", required=False)
    current_city = forms.CharField(help_text="Please enter your current city.", required=False)

    MALE = 'M'
    FEMALE = 'F'
    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    )

    gender = forms.ChoiceField(widget=forms.RadioSelect, help_text="Please select your gender.", required=False,
                               choices=GENDER)

    birthday = forms.DateField(widget=SelectDateWidget, help_text="Please enter your birth date.", required=False)
    about_me = forms.CharField(help_text="Please give a description about yourself.", required=False)
    website = forms.CharField(help_text="Please enter your website.", required=False)

    class Meta:
        model = UserProfile
        fields = ['gender', 'website', 'current_city', 'birthday', 'about_me', 'picture']

