from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import SearchForm, ExtendForm
from .models import Author, Book, Publication, UserStaff, RegisterEntry, ExtendLog
from datetime import timedelta


def index(request):
    if not request.user.is_authenticated():
        return render(request, "unlogged_home.html")
    user_staff = UserStaff.objects.filter(user=request.user).all()
    # if user_staff:
    # render a staff homepage instead
    # return render(request, "homepage.html", {"staff": True})
    # form = SearchForm()
    # TODO: this also displays returned books, fix later
    reg_entries = [i for i in list(
        RegisterEntry.objects.all()) if i.user]
    borrowed_entries = [
        i for i in reg_entries if i.user.username == request.user.username]
    ctx = {"form": SearchForm(), "borrowed_entries": borrowed_entries}
    return render(request, "homepage.html", ctx)


# Staff flows
# checkout
# @login_required
# def checkout(request):
#     user_staff = UserStaff.objects.filter(user=request.user).all()
#     if not user_staff:
#         return HttpResponseForbidden()
#     form = CheckoutForm()
#     return render(request, "checkout.html", {"form": form})
# return
# view
def view_books(request):
    user_staff = UserStaff.objects.filter(user=request.user).all()
    if not user_staff:
        return HttpResponseForbidden()
    borrowed_entries = list(RegisterEntry.objects.all())

    return render(request, "borrowed_books.html", {"entries": borrowed_entries})

# User flows
# search
@login_required
def search(request):
    form = None
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            # process here
            books = Book.objects.filter(
                publication__title__search=form.cleaned_data["search_text"])

            ctx = {
                "form": form,
                "results": books,
                "search_text": form.cleaned_data["search_text"]
            }
            return render(request, "search.html", ctx)
    else:
        form = SearchForm()
    return render(request, "search.html", {"form": form})

# extend
@login_required
def extend(request, slug, acc):
    book = Book.objects.get(acc=acc)
    # the most recent action will be borrow
    # otherwise the user will not come to this
    # page. TODO: safeguard this
    regentry = RegisterEntry.objects.filter(
        book=book, action="borrow")[0]
    form = None
    if request.method == "POST":
        form = ExtendForm(request.POST)
        if form.is_valid():
            # process here
            x = form.cleaned_data["return_date"]
            most_recent_log = regentry.most_recent_extendlog
            e = ExtendLog(original_returndate=most_recent_log.original_returndate,
                          current_returndate=most_recent_log.current_returndate + timedelta(x))
            e.save()
            regentry.most_recent_extendlog = e
            regentry.save()
            return redirect("index")
    else:
        form = ExtendForm()
    return render(request, "extend.html", {"form": form, "book": book})
# view
@login_required
def view_one_book(request, slug, acc):
    book = Book.objects.get(acc=acc)
    ctx = {"book": book}
    return render(request, "book.html", ctx)
