from django import forms


class LoginForm(forms.Form):
    wechat_id = forms.CharField(max_length=100, label='wechat_id')
    password = forms.CharField(max_length=255, label='password')


class RegisterForm(forms.Form):
    wechat_id = forms.CharField(max_length=100, label='wechat_id')
    name = forms.CharField(max_length=100, label='name')
    password = forms.CharField(max_length=255, label='password')


class ChangePasswordForm(forms.Form):
    wechat_id = forms.CharField(max_length=100, label='wechat_id')
    password = forms.CharField(max_length=255, label='password')
    new_password = forms.CharField(max_length=255, label='new_password')


class ContactForm(forms.Form):
    alias = forms.CharField(max_length=255, label='alias')
    tag = forms.CharField(max_length=32, label='tag')
    mobile = forms.CharField(max_length=32, label='mobile')
    description = forms.CharField(max_length=255, label='description')
    source = forms.CharField(max_length=255, label='source')


class AddContactForm(forms.Form):
    wechat_id = forms.CharField(max_length=255, label='wechat_id')


class ChangeProfileForm(forms.Form):
    name = forms.CharField(max_length=255, label='name')
    gender = forms.ChoiceField(label='gender')
    region = forms.CharField(max_length=255, label='region')
    whats_up = forms.CharField(max_length=255, label='whats_up')
    phone = forms.CharField(max_length=255, label='phone')
    email = forms.EmailField(max_length=255, label='email')


class AddOAForm(forms.Form):
    oa_name = forms.CharField(max_length=255, label='oa_name')

class AdminForm(forms.Form):
    admin_id = forms.CharField(max_length=255,label='admin_id')
    password = forms.CharField(max_length=255, label='password')