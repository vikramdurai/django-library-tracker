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
<<<<<<< HEAD
        books.extend(list(Book.objects.filter(publication=i).all()))
=======
        books.extend(list(Books.objects.filter(publication=i).all()))
>>>>>>> 8ff3536185f64245a4e0752f97a39bc411b36ff9
    return books
