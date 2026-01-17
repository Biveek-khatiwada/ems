from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, Department


class CustomUserCreationForm(forms.ModelForm):
    """
    Form for creating a new CustomUser with associated Django User.
    """
  
    username = forms.CharField(
        max_length=150,
        required=True,
        help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.")
    )
    
    email = forms.EmailField(
        required=True,
        help_text=_("Required. Enter a valid email address.")
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        help_text=_("Optional.")
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=False,
        help_text=_("Optional.")
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        label=_("Password"),
        help_text=_("Enter a strong password.")
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label=_("Password Confirmation"),
        help_text=_("Enter the same password as before, for verification.")
    )
    
    
    phone_number = forms.IntegerField(
        required=True,
        help_text=_("Enter 10-15 digit phone number"),
        widget=forms.NumberInput(attrs={'placeholder': '9876543210'})
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label=_("Select Department")
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        max_length=100,
        required=True,
        help_text=_("Maximum 100 characters")
    )
    
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        initial='employee'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'department', 'address', 'role', 'is_active'
        ]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(_("A user with that username already exists."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("A user with that email already exists."))
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        
        
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise ValidationError(_("A user with this phone number already exists."))
        
        phone_str = str(phone_number)
        if len(phone_str) < 10 or len(phone_str) > 15:
            raise ValidationError(_("Phone number must be between 10 and 15 digits."))
        
        return phone_number

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Passwords don't match."))
        
       
        if len(password1) < 8:
            raise ValidationError(_("Password must be at least 8 characters long."))
        
        return password2

    def save(self, commit=True):
       
        user_data = {
            'username': self.cleaned_data['username'],
            'email': self.cleaned_data['email'],
            'first_name': self.cleaned_data.get('first_name', ''),
            'last_name': self.cleaned_data.get('last_name', ''),
        }
        
        user = User(**user_data)
        user.set_password(self.cleaned_data['password1'])
        
        if commit:
            user.save()
            
      
            custom_user = super().save(commit=False)
            custom_user.user = user
            custom_user.save()
            
            
            self.save_m2m()
            
            return custom_user
        
        return user


# forms.py

from django import forms
from .models import Department, CustomUser

class DepartmentForm(forms.ModelForm):
    manager = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__in=['manager', 'admin'], is_active=True),
        required=False,
        empty_label="Select Manager"
    )
    
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'manager', 'is_active']
        
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()  # Convert to uppercase
            # Check for uniqueness (excluding current instance if editing)
            qs = Department.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Department code already exists.')
        return code
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Check for uniqueness (excluding current instance if editing)
        qs = Department.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Department name already exists.')
        return name