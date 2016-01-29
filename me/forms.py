# -*- coding: utf-8 -*-

__author__ = 'Mbogning Rodrigue'

from django import forms
#from captcha.fields import ReCaptchaField


class MemberForm(forms.Form):
    phone = forms.CharField(max_length=18)
    email = forms.EmailField()
    password = forms.CharField(max_length=30)
    password1 = forms.CharField(max_length=30)


class DomainRegistrationForm(forms.Form):
    customer_name = forms.CharField(max_length=100)
    domain_type = forms.CharField(max_length=25)
    company = forms.CharField(max_length=100)
    domain_name = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=18)
    storage = forms.CharField(max_length=18)
    email = forms.EmailField()


class PasswordResetForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField()
    #captcha = ReCaptchaField()


