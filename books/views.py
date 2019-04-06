from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .forms import SearchForm
from .models import Author, Book, UserStaff


@login_required
def index(request):
    user_staff = UserStaff.objects.filter(user=request.user).all()
    # print(user_staff)
    # if user_staff:
    # render a staff homepage instead
    # return render(request, "homepage.html", {"staff": True})
    return render(request, "homepage.html")


@login_required
def search(request):
    form = None
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            # process here
            results = Book.objects.filter(
                title__search=form.cleaned_data["search_text"])
            ctx = {
                "form": form,
                "results": results,
                "search_text": form.cleaned_data["search_text"]
            }
            return render(request, "search.html", ctx)
    else:
        form = SearchForm()
    return render(request, "search.html", {"form": form})
