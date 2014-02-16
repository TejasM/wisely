from django import forms
from django.forms.extras.widgets import SelectDateWidget

from models import UserProfile, User


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
    headline = forms.CharField(required=False)
    about_me = forms.CharField(required=False)
    website = forms.URLField(initial='http://', help_text="Please enter your website.", required=False)

    class Meta:
        model = UserProfile
        #fields = ['gender', 'website', 'current_city', 'birthday', 'headline', 'about_me', 'picture']
        fields = ['gender', 'website', 'current_city', 'headline', 'about_me']


class UserForm(forms.ModelForm):
    email = forms.CharField(help_text="Please enter your email.", required=False)

    class Meta:
        model = User
        fields = ['email']
