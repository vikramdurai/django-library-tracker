from django import forms
from .models import Borrower


class SearchForm(forms.Form):
    search_text = forms.CharField(label="", max_length=200, widget=forms.TextInput(
        attrs={'placeholder': 'Search'}))


# class CheckoutForm(forms.Form):
#     acc = forms.CharField(label="Accession number", max_length=200)
#     borrower = forms.ChoiceField(
#         label="Borrower", choices=((i.slug, i.name) for i in Borrower.objects.all()))

class ExtendForm(forms.Form):
    return_date = forms.IntegerField()
