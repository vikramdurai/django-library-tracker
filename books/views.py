from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import SearchForm, ExtendForm, CheckoutForm, UserStaffForm, NewBookForm, NewPubForm, ChooseLibraryForm
from .models import Library, Author, Book, Publication, UserStaff, UserMember, RegisterEntry, ExtendLog, Borrower
from datetime import timedelta


def staff(request):
    user_staff = UserStaff.objects.get(user=request.user)
    if user_staff:
        return user_staff
    return False


def choose_library(request):
    if request.user.social_auth.exists():
        return redirect("index")
    form = None
    if request.method == "POST":
        form = ChooseLibraryForm(request.POST)
        if form.is_valid():
            lb = Library.objects.get(id=form.cleaned_data["library"])
            user_member = UserMember(user=request.user, library=lb)
            user_member.save()
            return redirect("index")
    else:
        form = ChooseLibraryForm()
    return render(request, "choose_library.html", {"form":form})


def index(request):
    if not request.user.is_authenticated():
        return render(request, "unlogged_home.html")
    user_staff = staff(request)
    if user_staff:
        # render a staff homepage instead
        return render(request, "staff_home.html", {"form": SearchForm(), "user": request.user, "u_staff": user_staff})
    reg_entries = RegisterEntry.get_all_borrowed_entries()
    borrowed_entries = [
        i for i in reg_entries if i.user.username == request.user.username]
    user_libraries = [
        i.library for i in UserMember.objects.all() if i.user == request.user]
    ctx = {"form": SearchForm(), "borrowed_entries": borrowed_entries,
           "user_libraries": user_libraries}
    return render(request, "homepage.html", ctx)

# Staff flows
# TODO: implement a staff decorator thingy
# new_book
@login_required
def new_book(request):
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden()
    form = None
    if request.method == "POST":
        form = NewBookForm(request.POST)
        if form.is_valid():
            b = Book(publication=Publication.objects.get(id=form.cleaned_data["publication"]),
                     date_added=timezone.now(), acc=form.cleaned_data["acc"], library=user_staff.library)
            b.save()
            return redirect("titles", slug=b.publication.slug, acc=b.acc)
    else:
        form = NewBookForm()
    return render(request, "newbook.html", {"form": form})


# new_publication
@login_required
def new_publication(request):
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden()
    form = None
    if request.method == "POST":
        form = NewPubForm(request.POST)
        if form.is_valid():
            p = Publication(
                sno=form.cleaned_data["sno"],
                title=form.cleaned_data["title"],
                author=Author.objects.get(id=form.cleaned_data["author"]),
                code=form.cleaned_data["code"],
                available_goodreads=form.cleaned_data["avgood"],
                genre=form.cleaned_data["genre"],
                slug="",
            )
            p.save()
            return render(request, "newpub.html", {"success": True, "form": form})
    else:
        form = NewPubForm()
    return render(request, "newpub.html", {"form": form})

# checkout
@login_required
def checkout(request, slug, acc):
    print(acc)
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden()
    form = None
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # process here
            re = RegisterEntry(book=Book.objects.get(acc=acc),
                               date=timezone.now(),
                               user=User.objects.get(
                                   username=form.cleaned_data["user"]),
                               borrower=Borrower.objects.get(
                                   slug=form.cleaned_data["borrower"]),
                               library=user_staff.library,
                               action="borrow")
            re.save()
            e = ExtendLog(new_returndate=timezone.now() + timedelta(form.cleaned_data["returndate"]),
                          returndate=re.most_recent_extendlog.returndate,
                          entry=re)
            e.save()
            return redirect("index")
    else:
        form = CheckoutForm()
    return render(request, "checkout.html", {"form": form, "book": Book.objects.get(acc=acc)})

# checkin
@login_required
def checkin(request, slug, acc):
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden()
    b = Book.objects.get(acc=acc)
    print(RegisterEntry.objects.get(book=b))
    print(RegisterEntry.objects.filter(library=user_staff.library))
    bre = RegisterEntry.objects.get(book=b, library=user_staff.library)
    re = RegisterEntry(book=b, date=timezone.now(),
                       user=bre.user, borrower=bre.borrower, action="return")
    re.save()
    return redirect("index")

# add new staff account
@login_required
def addstaff(request):
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden()
    form = None
    if request.method == "POST":
        form = UserStaffForm(request.POST)
        if form.is_valid():
            u = User.objects.get(username=form.cleaned_data["username"])
            UserStaff(user=u, library=user_staff.library).save()
            return redirect("index")
    else:
        form = UserStaffForm()
    return render(request, "addstaff.html", {"form": form})

# view
@login_required
def view_books(request):
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden()
    return render(request, "borrowed_books.html", {"entries": RegisterEntry.get_all_borrowed_entries()})

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
    regentry = RegisterEntry.objects.filter(
        book=book, action="borrow")[0]
    form = None
    if request.method == "POST":
        form = ExtendForm(request.POST)
        if form.is_valid():
            # process here
            x = form.cleaned_data["return_date"]
            e = ExtendLog(entry=regentry, returndate=regentry.most_recent_extendlog.returndate,
                          new_returndate=regentry.most_recent_extendlog.new_returndate + timedelta(x))
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
    user_staff = UserStaff.objects.filter(user=request.user).all()
    ctx = None
    if not user_staff:
        ctx = {"book": book}
    else:
        ctx = {"book": book, "user_staff": True}
    return render(request, "book.html", ctx)

def bye_bye(request):
    return render(request, "bye.html")
