from django import template
from books.forms import UserJoinApproveForm
from books.models import Book
register = template.Library()


@register.simple_tag
def get_form(theo):
    return UserJoinApproveForm({'id': theo})


@register.simple_tag
def books_by_author(a):
    publications = a.books()
    books = []
    for i in publications:
        books.extend(list(Book.objects.filter(publication=i).all()))
    return books
