from django import forms 
from django.contrib.auth.models import User 
from django.contrib.auth.forms import UserCreationForm, UserChangeFrom 
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import CustomUser,Department


class CustomUserCreationForm(forms.ModelForm):
    """
    Form for creating a new CustomUser 
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        help_text = _("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.")
    )
    email = forms.EmailField(
        required=True,
        help_text = _("Required. Enter a valid email address.")
    )
    
    first_name = forms.ChatField(
        max_length=30,
        required=True,
        help_text = _("Required. 30 characters or fewer.")
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        help_text = _("Required. 30 characters or fewer.")
    )
    password1 = forms.CharField(
        wiget=forms.passwordInput,
        label= _("password"),
        help_text = _("enter a strong password.")
    )
    password2 = forms.CharField(
        widget = forms.PasswordInput,
        label = _("password confirmation"),
        help_text = _("Enter the same password as before, for verification.")
    )
    
    phone_number = forms.IntegerField(
        required=True,
        help_text = _("enter 10 digit phone number."),
        widget=forms.NumberInput(attrs={'placeholder':'9876543210'})
        
    )
    department = forms.ModelChoiceField(
        queryset = Department.objects.all(),
        required=True,
        empty_label=_("select department")
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows':3}),
        max_length=100,
        required=True,
        help_text = _("maximum 100 characters.")
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        initial="employee",
        required=True
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
    )
    
    class Meta:
        model = CustomUser
        fields =['username','email','first_name','last_name','phone_number','department','address','role','is_active']
        
    def cleam_username(self):
        username = self.cleanned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError(_("A user with that username already exists."))
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("A user with that email already exists"))
        return email
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise ValidationError(_("A User with that phone number already exists."))
        
        phone_str = str(phone_number)
        if len(phone_str) <10 or len(phone_str)>15:
            raise ValidationError(_("phone number must be between 10 and 15 digits."))
        return phone_number
    
    def clean_password2(self):
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 and password2 and password1 !=password2:
            raise ValidationError(_("the two password fields didn't match."))
        
        if len(password1) < 8:
            raise ValidationError(_("password must be at least 8 characters long."))
        return password2
    
    def save(self,commit=True):
        user_data ={
            'username':self.cleaned_data['username'],
            'email':self.cleaned_data['email'],
            'first_name':self.cleaned_data['first_name'],
            'last_name':self.cleaned_data['last_name'],
        }
        user = User(**user_data)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            custom_user =super().save(commit=False)
            custom_user.user = user 
            custom_user.save()
            self.save_m2m()
            return custom_user
        return user