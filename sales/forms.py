# -*- coding: utf-8 -*-

__author__ = 'Mbogning Rodrigue'

from django import forms


class RefillForm(forms.Form):
    beneficiary = forms.CharField(max_length=50)
    amount = forms.IntegerField()


class CreateRetailerForm(forms.Form):
    retailer = forms.CharField(max_length=150)
    password = forms.CharField(max_length=150)
    password_confirm = forms.CharField(max_length=150)


class RefillPrepaidCustomerForm(forms.Form):
    beneficiary = forms.CharField(max_length=50)
    bundle_id = forms.IntegerField()
    duration = forms.IntegerField()

