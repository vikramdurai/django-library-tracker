from django import forms
from django.contrib.auth.models import User
from .models import Borrower
from django.core.validators import MaxValueValidator


class SearchForm(forms.Form):
    search_text = forms.CharField(label="", max_length=200, widget=forms.TextInput(
        attrs={'placeholder': 'Search'}))


class CheckoutForm(forms.Form):
    borrower = forms.ChoiceField(
        label="Borrower", choices=((i.slug, i.name) for i in Borrower.objects.all()))
    user = forms.CharField(label="", max_length=200, widget=forms.TextInput(
        attrs={"placeholder": "Search users", "class": "ui search"}))
    returndate = forms.IntegerField(
        label="Return date (user can extend later)")


class ExtendForm(forms.Form):
    # they shouldn't extend by more than
    # a week
    return_date = forms.IntegerField(validators=[MaxValueValidator(7)])
