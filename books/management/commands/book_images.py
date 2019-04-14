from django.core.management import BaseCommand, CommandError
from urllib.request import urlopen
from urllib.parse import quote
from urllib.error import HTTPError
from urllib.request import retrieve
from json import loads
from time import sleep
from books.models import *


class Command(BaseCommand):
    help = "Scrapes images from the web for all titles in the database"

    def add_arguments(self, parser):
        parser.add_argument("--all",
                            help="Import all book titles", action="store_true")
        parser.add_argument("--title", type=str,
                            help="Specific book title to import image of")

    def handle(self, *args, **options):
        if options["all"]:
            books = Publication.objects.all()
            iteration = 0
            _i = len(books)
            print("Number of books to process:", len(books))
            print("Processing 0 of", _i, end="\r")

            def do(iteration=iteration, _i=_i):
                for i in books[iteration:]:
                    try:
                        data = urlopen(
                            "https://www.googleapis.com/books/v1/volumes?q=title:"+quote(i.title), data=None, timeout=5)
                        _i -= 1
                        print("Processing", _i, "of", len(books), end="\r")
                        retrieve(loads(data.read())[
                                 "thumbnail"], "image_"+i.slug+".jpg")

                    except HTTPError as e:
                        if "403" in str(e):
                            sleep(3)
                            # this code skips most of the already-processed
                            # books
                            iteration += 1
                            print("iterating")
                            do()
                        else:
                            print("Error:", e)
            do()
            print("\nFinished!")
        elif options["title"]:
            p = Publication.objects.get(title=options["title"])
            try:
                data = urlopen(
                    "https://www.googleapis.com/books/v1/volumes?q=title:"+quote(p.title), data=None, timeout=5)
                retrieve(urlopen(loads(data.read())[
                         "thumbnail"]), "image_"+i.slug+".jpg")
            except HTTPError as e:
                print("Error:", e)
