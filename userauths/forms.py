from django import forms
from django.contrib.auth.forms import UserCreationForm
from userauths.models import Profile, User, GENDER

#create a form
class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': '', 'id': "", 'placeholder':'Full Name', "class":"with-border"}), max_length=100, required=True)
    username = forms.CharField(widget=forms.TextInput(attrs={'class': '', 'id': "", 'placeholder':'Username'}), max_length=100, required=True)
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': '', 'id': "", 'placeholder':'Mobile No.'}), max_length=100, required=True)
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': '' , 'id': "", 'placeholder':'Email Address'}), required=True)
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'id': "", 'placeholder':'Password'}), required=True)
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'id': "", 'placeholder':'Confirm Password'}), required=True)

    class Meta:
        model = User
        #apa yg hg nak mintak user to register
        fields = ['full_name', 'username', 'email', 'phone', 'gender', 'password1', 'password2'] #refer model user to check

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields(): #loop thru all the forms yg kita ada under userregisterform
            visible.field.widget.attrs['class'] = 'with-border'
            # visible.field.widget.attrs['placeholder'] = visible.field.label

class ProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'with-border'}))
    full_name = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'with-border'}))
    email = forms.EmailField(required=False, widget=forms.TextInput(attrs={'class': 'with-border', 'readonly': 'readonly'}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'with-border'}), required=False)
    gender = forms.ChoiceField(choices=GENDER, widget=forms.Select(attrs={'class': 'with-border'}), required=False)

    class Meta:
        model = Profile
        fields = ['full_name', 'phone', 'gender']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        if self.user and username != self.user.username:
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("This username is already taken. Please choose another one.")
        return username
