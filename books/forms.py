from django import forms


class SearchForm(forms.Form):
    search_text = forms.CharField(label="Search", max_length=200)
