from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.utils import timezone
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder

from .forms import SearchForm, ExtendForm, CheckoutForm, UserStaffForm, NewBookForm, NewPubForm, UserConfigForm
from .models import Library, Series, Genre, Author, Book, Publication, UserStaff, UserMember, UserJoinRequest, RegisterEntry, ExtendLog, Borrower
from datetime import timedelta, datetime
from json import dumps
from .utils import *
import xlsxwriter
import io


def staff(request):
    try:
        user_staff = UserStaff.objects.get(user=request.user)
        if user_staff:
            return user_staff
    except:
        pass
    return False


def send_html_email(to_list, subject, template_name, context, sender=settings.DEFAULT_FROM_EMAIL):
    msg_html = render_to_string(template_name, context)
    msg = EmailMessage(subject=subject, body=msg_html,
                       from_email=sender, to=to_list)
    msg.content_subtype = "html"  # Main content is now text/html
    return msg.send()


def index(request):
    if not request.user.is_authenticated():
        return render(request, "unlogged_home.html")
    user_members = UserMember.objects.filter(user=request.user).all()
    user_requests = UserJoinRequest.objects.filter(
        user=request.user, approved=False).all()
    if user_members.exists():
        user_staff = staff(request)
        if user_staff:
            # render a staff homepage instead
            return render(request, "staff_home.html", {"form": SearchForm(), "user": request.user, "user_staff": user_staff})
        reg_entries = RegisterEntry.get_all_borrowed_entries()
        borrowed_entries = [
            i for i in reg_entries if i.user and i.user.user.username == request.user.username]
        user_libraries = [i.library for i in user_members]
        ctx = {"form": SearchForm(), "borrowed_entries": borrowed_entries,
               "user_libraries": user_libraries}
        return render(request, "homepage.html", ctx)

    elif list(user_requests) != []:
        return render(request, "unapproved_home.html", {"user": user_requests[0].user, "library": user_requests[0].library})
    else:
        form = None
        lb = None
        b = None
        if request.method == "POST":
            form = UserConfigForm(request.POST)

            if form.is_valid():
                lb = Library.objects.get(id=form.cleaned_data["library"])
                b = form.cleaned_data["borrower"]
                if lb and not b:
                    form = UserConfigForm(
                        {"library": [lb.id, lb.name], "borrower": ""}, auto_id=False)
                    return render(request, "userconfig.html", {"form": form, "show_borrower": True})
                else:
                    b = Borrower.objects.filter(name=b)
                    if list(b) != []:
                        b = b[0]
                    else:
                        b = Borrower(name=b, slug=slugify(b))
                        b.save()
                    user_member = UserJoinRequest(
                        user=request.user, library=lb, borrower=b)
                    user_member.save()
                    return redirect("index")
        else:
            form = UserConfigForm()
        return render(request, "userconfig.html", {"form": form})


def api_homepage(request):
    from django.contrib.staticfiles.templatetags.staticfiles import static

    def dictify(i):
        print("debug: i is", i)
        reg = RegisterEntry.get_all_borrowed_entries().filter(book=i)
        b = None
        if reg.exists():
            b = reg.first().borrower.name
        return {
            "author": i.publication.author.name,
            "ongoodreads": i.publication.available_goodreads,
            "book_url": static("books/image_%s.jpg" % i.publication.slug),
            "publication": i.publication.title,
            "is_borrowed": RegisterEntry.is_borrowed(i),
            "borrower": b,
            "date_added": i.date_added,
            "book_acc": i.acc,
            "book_genre": i.publication.genre,
            "library": i.library.name
        }
    query = request.GET.get("query", "")
    _results = list(Book.objects.all())[:10]
    resp = None
    results = [dictify(i) for i in _results[:10]]
    if not query:
        resp = dumps({"results": results}, cls=DjangoJSONEncoder)
        return HttpResponse(resp, status=200, content_type="application/json")
    _results = list(Book.objects.filter(Q(publication__title__icontains=query) | Q(
        publication__author__name__icontains=query)))[:10]
    results = [dictify(i) for i in _results]
    resp = dumps({"results": results}, cls=DjangoJSONEncoder)
    return HttpResponse(resp, status=200, content_type="application/json")

# Staff flows

# verify users


def pending_requests(request):
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden()
    user_requests = UserJoinRequest.objects.filter(
        approved=False, library=user_staff.library).all()
    return render(request, "userrequests.html", {"user_join_requests": user_requests, "user_staff": user_staff})

# will only be used by javascript


def api_search(request):
    b = None
    origin = request.GET.get("origin", "")
    if not origin:
        return HttpResponse(dumps({"msg": "Error, no origin set"}), status=400, content_type="application/json")
    if origin == "userconfig":
        b = request.GET.get("name", "")
        results = Borrower.objects.filter(name__icontains=b.split()[
                                          0]).values_list("name")[:10]
        return HttpResponse(dumps({'results': list(results)}), status=200, content_type="application/json")
    elif origin == "checkout":
        b = request.GET.get("name", "")
        results = []
        search_ = UserMember.objects.filter(
            Q(user__username__istartswith=b) | Q(borrower__name__istartswith=b)).all()
        search_b = Borrower.objects.filter(name__icontains=b).all()
        print(search_b)
        for i in search_:
            results.append({
                "title": i.user.username,
                "description": i.borrower.name,
            })
        for i in search_b:
            results.append({
                "title": str(i),
                "description": str(i),
            })
        return HttpResponse(dumps({'results': list(results)}), status=200, content_type="application/json")

    elif origin == "books":
        b = request.GET.get("name", "")
        results = [{"title": "%s (%s)" % (i.publication.title, i.acc),
                    "description": i.publication.author.name,
                    "acc": i.acc} for i in Book.objects.filter(publication__title__istartswith=b)]
        return HttpResponse(dumps({'results': list(results)}), status=200, content_type="application/json")

    elif origin == "authors":
        b = request.GET.get("name", "")
        results = Author.objects.filter(name__icontains=b).values_list("name")
        return HttpResponse(dumps({'results': list(results)}), status=200, content_type="application/json")

    elif origin == "titles":
        b = request.GET.get("name", "")
        results = [{"title": "%s" % i.title,
                    "description": i.author.name} for i in Publication.objects.filter(title__istartswith=b)]
        return HttpResponse(dumps({'results': list(results)}), status=200, content_type="application/json")
    return HttpResponse(dumps({"msg": "Error, invalid origin"}), status=400, content_type="application/json")

# will only be used by javascript


def approve_requests(request):
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden
    u = request.POST.get("id", None)
    try:
        b = UserJoinRequest.objects.get(id=u)
    except:
        return redirect("pendingrequests")
    um = UserMember(user=b.user, library=b.library, borrower=b.borrower)
    try:
        um.save()
    except:
        return redirect("pendingrequests")
    try:
        b.approved = True
        b.save()
    except:
        return redirect("pendingrequests")
    return redirect("pendingrequests")


@login_required
def export_data(request):
    which = request.GET.get("which")
    output = io.BytesIO()
    if which == "series":
        s_string = "100 600 700 800 900"

        nseries_names = s_string.split()
        workbook = xlsxwriter.Workbook(output)
        w = workbook.add_worksheet("CATALOGUE KEY")
        ckdata = export_key()
        for row_num, columns in enumerate(ckdata):
            for col_num, cell_data in enumerate(columns):
                w.write(row_num, col_num, cell_data)
        print("wrote the catalogue key")
        for name in nseries_names:
            data, ok = export_from_series(name)
            if not ok:
                break
            s = Series.objects.get(num=name)
            worksheet = workbook.add_worksheet(
                str(s.num)[0]+"_"+s.desc.upper().replace(" ", "_"))
            for row_num, columns in enumerate(data):
                for col_num, cell_data in enumerate(columns):
                    worksheet.write(row_num, col_num, cell_data)
            print("Done:", str(s))
        workbook.close()
        output.seek(0)
    else:
        workbook = xlsxwriter.Workbook(output)
        w = workbook.add_worksheet(
            "overdue-"+datetime.strftime(datetime.today(), "%b'%y").lower())  # overdue-nov'19
        data = export_register()
        for row_num, columns in enumerate(data):
            for col_num, cell_data in enumerate(columns):
                w.write(row_num, col_num, cell_data)
        print("Done.")
        workbook.close()
        output.seek(0)
     # Set up the Http response.
    dstring = datetime.today().strftime("%d%m%Y")
    filename = None
    if which == "series":
        filename = 'ML_Catalogue_%s.xlsx' % dstring
    else:
        filename = "Malhar_Library_Register_%s.xlsx" % dstring
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


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
            b = Book(publication=Publication.objects.get(title=form.cleaned_data["publication"]),
                     date_added=timezone.now(), acc=form.cleaned_data["acc"], library=user_staff.library)
            b.save()
            return redirect("titles", slug=b.publication.slug, acc=b.acc)
    else:
        form = NewBookForm()
    return render(request, "newbook.html", {"form": form, "user_staff": user_staff})


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
            a = None
            try:
                a = Author.objects.get(name=form.cleaned_data["author"])
            except Author.DoesNotExist:
                a = Author(name=form.cleaned_data["author"])
                a.save()
            p = Publication(
                sno=form.cleaned_data["sno"],
                title=form.cleaned_data["title"],
                author=a,
                code=form.cleaned_data["code"],
                available_goodreads=form.cleaned_data["avgood"],
                genre=form.cleaned_data["genre"],
                isbn=form.cleaned_data["isbn"],
                slug="",
            )
            if not Publication.objects.filter(isbn=p.isbn).empty():
                ctx = {"success": False, "form": form, "user_staff": user_staff,
                       "error": "A book with this ISBN already exists."}
                return render(request, "newpub.html", ctx)
            if not Publication.objects.filter(code=p.code).empty():
                ctx = {"success": False, "form": form, "user_staff": user_staff,
                       "error": "A book with this code already exists."}
                return render(request, "newpub.html", ctx)
            p.save()
            return render(request, "newpub.html", {"success": True, "form": form, "user_staff": user_staff})
    else:
        form = NewPubForm()
    return render(request, "newpub.html", {"form": form, "user_staff": user_staff})

# checkout
@login_required
def checkout(request):
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden()
    form = None
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # process here
            book = Book.objects.filter(acc=form.cleaned_data["acc"])
            if book.exists():
                if RegisterEntry.is_borrowed(book[0]):
                    return render(request, "checkout.html", {"form": form, "user_staff": user_staff, "error": "Already borrowed book"})
                else:
                    # create a new register entry
                    borrowing_user = User.objects.filter(
                        username=form.cleaned_data["user"])
                    borrower = None
                    if not borrowing_user.exists():
                        borrower = Borrower.objects.filter(
                            name=form.cleaned_data["user"]).first()
                        if not borrower:
                            return render(request, "checkout.html", {"form": form, "user_staff": user_staff, "error": "No member exists with that username"})
                    member_who_borrowed_this_book = None
                    if borrowing_user.exists():
                        member_who_borrowed_this_book = UserMember.objects.filter(
                            user=borrowing_user[0], library=user_staff.library).first()
                        re = RegisterEntry(book=book[0],
                                           date=timezone.now(),
                                           user=member_who_borrowed_this_book,
                                           borrower=member_who_borrowed_this_book.borrower,
                                           library=user_staff.library,
                                           action="borrow")
                        re.save()
                    else:
                        re = RegisterEntry(book=book[0],
                                           date=timezone.now(),
                                           user=None,
                                           borrower=borrower,
                                           library=user_staff.library,
                                           action="borrow")
                        re.save()
                    # def lol(to_list, subject, template_name, context, sender=settings.DEFAULT_FROM_EMAIL):
                    #     msg_html = render_to_string(template_name, context)
                    #     msg = EmailMessage(subject=subject, body=msg_html, from_email=sender, bcc=to_list)
                    #     msg.content_subtype = "html"  # Main content is now text/html
                    #     return msg.send()
                    # print("User email:", borrowing_user[0].email)
                    # print("Username:", borrowing_user[0].username)
                    # send_html_email(to_list=[borrowing_user[0].email],subject="You've borrowed a book - Everylibrary.co",template_name="email.html",sender=settings.EMAIL_HOST_USER,context={"user": borrowing_user, "entry": re, "book": book[0], "library": user_staff.library})
                    return redirect("index")
            else:
                return render(request, "checkout.html", {"form": form, "user_staff": user_staff})
            # e = ExtendLog(new_returndate=timezone.now() + timedelta(form.cleaned_data["returndate"]),
            #               returndate=re.most_recent_extendlog.returndate,
            #               entry=re)
            # e.save()

    else:
        form = CheckoutForm()
    return render(request, "checkout.html", {"form": form, "user_staff": user_staff})

# checkin
@login_required
def checkin(request, slug, acc):
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden()
    b = Book.objects.get(acc=acc)
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
    return render(request, "addstaff.html", {"form": form, "user_staff": user_staff})

# view
@login_required
def view_books(request):
    user_staff = staff(request)
    if not user_staff:
        return HttpResponseForbidden()
    context = {
        # "entries": RegisterEntry.get_all_borrowed_entries(),
        "user_staff": user_staff
    }
    return render(request, "borrowed_books.html", context)


@login_required
def api_view_borrowed_books(request):
    def regEntryToDict(r):
        return {
            "publication": r.book.publication.title,
            "pub-string": r.book.publication.slug,
            "book-acc": r.book.acc,
            "borrower": r.borrower.name,
            "borrow-date": r.date,  # until we fix extendlog TODO
        }
    query = request.GET.get("query", "")
    sample = RegisterEntry.get_all_borrowed_entries().all()
    regentry_books = sample.filter(
        book__publication__title__icontains=query).all()
    regentry_borrowers = sample.filter(borrower__name__icontains=query).all()
    final_books = [regEntryToDict(i) for i in list(regentry_books)]
    final_borrowers = [regEntryToDict(
        i) for i in regentry_borrowers if i not in list(regentry_books)]
    if not query:
        return HttpResponse(dumps({'results': [regEntryToDict(i) for i in list(sample)] + final_borrowers}, cls=DjangoJSONEncoder), status=200, content_type="application/json")
    resp = dumps({"results": final_books + final_borrowers},
                 cls=DjangoJSONEncoder)
    return HttpResponse(resp, status=200, content_type="application/json")

# User flows
# search
@login_required
def search(request):
    form = None
    user_staff = staff(request)
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            # process here
            books = Book.objects.filter(
                publication__title__search=form.cleaned_data["search_text"])
            authors = Author.objects.filter(
                name__search=form.cleaned_data["search_text"])
            books_from_authors = dict()

            def books_by_author_f(a):
                publications = a.books.all()
                books = []
                for i in publications:
                    books.extend(
                        list(Book.objects.filter(publication=i).all()))
                return books
            for i in authors:
                books_from_authors[i.name] = books_by_author_f(i)
            ctx = {
                "form": form,
                "book_results": books,
                "user_staff": user_staff,
                "author_results": authors,
                "search_text": form.cleaned_data["search_text"],
                "books_from_authors": books_from_authors
            }
            return render(request, "search.html", ctx)
    else:
        form = SearchForm()
    return render(request, "search.html", {"form": form, "user_staff": user_staff})

# extend
@login_required
def extend(request, slug, acc):
    book = Book.objects.get(acc=acc)
    user_staff = staff(request)
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
    return render(request, "extend.html", {"form": form, "book": book, "user_staff": user_staff})
# view
@login_required
def view_one_book(request, slug, acc):
    from django.contrib.staticfiles.templatetags.staticfiles import static
    book = Book.objects.get(acc=acc)
    book_image = static("books/" + book.publication.slug + ".jpg")
    user_staff = UserStaff.objects.filter(user=request.user).all()
    ctx = {"book": book, "user_staff": user_staff, "book_image": book_image}
    return render(request, "book.html", ctx)


def bye_bye(request):
    return render(request, "bye.html")
