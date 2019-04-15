from django import forms
from django.contrib.auth.models import User
from .models import Author, Book, Publication, Borrower, Library, UserStaff
from django.core.validators import MaxValueValidator


class SearchForm(forms.Form):
    search_text = forms.CharField(label="", max_length=200, widget=forms.TextInput(
        attrs={'placeholder': 'Search'}))


class CheckoutForm(forms.Form):
    # USER_CHOICES = [[i.username, i.username] for i in User.objects.all()]
    USER_CHOICES = []
    BORROWER_CHOICES = [[i.slug, i.name] for i in Borrower.objects.all()]
    borrower = forms.ChoiceField(
        label="Borrower", choices=BORROWER_CHOICES, widget=forms.Select(
            attrs={"class": "ui search selection dropdown"}, choices=BORROWER_CHOICES))
    user = forms.ChoiceField(label="", choices=USER_CHOICES, widget=forms.Select(
        attrs={"class": "ui search selection dropdown"}, choices=USER_CHOICES))
    returndate = forms.IntegerField(
        label="Return date (user can extend later) ", widget=forms.NumberInput(attrs={"class": "ui"}))


class ExtendForm(forms.Form):
    # they shouldn't extend by more than
    # a week
    return_date = forms.IntegerField(validators=[MaxValueValidator(7)])


class UserStaffForm(forms.Form):
    # USER_CHOICES = [[i.username, i.username]
                    # for i in User.objects.all() if not UserStaff.objects.filter(user=i) and not (i.username == "admin")]
    USER_CHOICES = []
    username = forms.ChoiceField(label="Which user to add", choices=USER_CHOICES, widget=forms.Select(
        attrs={"class": "ui search selection dropdown"}, choices=USER_CHOICES))


class NewBookForm(forms.Form):
    PUBLICATION_CHOICES = [[i.id, i.title] for i in Publication.objects.all()]
    publication = forms.ChoiceField(label="Publication/title", choices=PUBLICATION_CHOICES, widget=forms.Select(
        attrs={"class": "ui search selection dropdown"}, choices=PUBLICATION_CHOICES))
    acc = forms.CharField(label="Accession number", max_length=255)


class NewPubForm(forms.Form):
    AUTHOR_CHOICES = [[i.id, i.name] for i in Author.objects.all()]
    author = forms.ChoiceField(label="Author", choices=AUTHOR_CHOICES, widget=forms.Select(
        attrs={"class": "ui search selection dropdown", "id": "b-author"}, choices=AUTHOR_CHOICES))
    avgood = forms.BooleanField(label="Available on Goodreads.com", widget=forms.CheckboxInput(
        attrs={"class": "ui checkbox"}))
    title = forms.CharField(label="Title", max_length=255, widget=forms.TextInput(
        attrs={"id": "b-title"}
    ))
    sno = forms.IntegerField(label="Special Number", widget=forms.TextInput(
        attrs={"id": "b-sno"}
    ))
    code = forms.CharField(label="Book code", max_length=255)
    genre = forms.CharField(label="Genre", max_length=255, widget=forms.TextInput(
        attrs={"id": "b-genre"}
    ))


class ChooseLibraryForm(forms.Form):
    LIBRARY_CHOICES = [[i.id, i.name] for i in Library.objects.all()]
    library = forms.ChoiceField(label="Available libraries", choices=LIBRARY_CHOICES, widget=forms.Select(
        attrs={"class": "ui search selection dropdown"}, choices=LIBRARY_CHOICES))
