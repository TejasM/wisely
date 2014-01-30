__author__ = 'Cheng'
from django import forms
from models import UserProfile


class UserProfileForm(forms.ModelForm):
    MALE = 'M'
    FEMALE = 'F'
    OTHER = 'O'
    UNKNOWN = 'U'
    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
        (OTHER, 'Other'),
        (UNKNOWN, 'Unspecified')
    )

    gender = forms.ChoiceField(widget=forms.RadioSelect, help_text="Please select your gender.", required=False,
                               choices=GENDER)
    website = forms.CharField(help_text="Please enter your website.", required=False)
    picture = forms.ImageField(help_text="Please select a profile image to upload.", required=False)

    class Meta:
        model = UserProfile
        fields = ['gender', 'website', 'picture']

