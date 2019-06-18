from django.core.management import BaseCommand, CommandError
from urllib.request import urlopen
from urllib.parse import quote
from urllib.error import HTTPError
from urllib.request import urlretrieve as retrieve
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
        try:
            if options["all"]:
                # don't process books with images
                books = Publication.objects.all().filter(img=None).all()
                iteration = 0
                _i = 0
                print("Number of books to process:", len(books))
                print("Processing", _i, "of", len(books), end="\r")

                def do(iteration=iteration, _i=_i):
                    for i in books[iteration:]:
                        try:
                            # don't process books with images
                            open("books/static/books/image_"+i.slug+".jpg")
                            i.img = "https://everylibrary.co/static/books/image_"+i.slug+".jpg"
                            i.save()
                            continue
                        except FileNotFoundError:
                            pass
                        try:
                            data = urlopen(
                                "https://www.googleapis.com/books/v1/volumes?q=title:"+quote(i.title), data=None, timeout=5)
                            _i += 1
                            print("Processing", _i, "of", len(books), end="\r")
                            b_data = loads(data.read())[
                                "items"][0]["volumeInfo"]
                            if not "imageLinks" in b_data:
                                # no image was available for this book
                                continue
                            retrieve(b_data["imageLinks"]["thumbnail"],
                                     "books/static/books/image_"+i.slug+".jpg")
                            i.img = "https://everylibrary.co/static/books/image_"+i.slug+".jpg"
                            i.save()

                        except HTTPError as e:
                            # we are not permitted to use the API
                            if "403" in str(e) or "503" in str(e):
                                # wait for a while
                                # the reason being that the
                                # Google Books API doesn't like
                                # being spammed
                                sleep(5)
                                # this code skips most of the already-processed
                                # books
                                iteration += 1
                                print(
                                    "Google books refusing to cooperate, retrying..", end="\n")
                                do()
                            else:
                                print("Error:", e)
                do()
                print("\nFinished!")
            elif options["title"]:
                print(options["title"])
                p = Publication.objects.get(slug=options["title"])
                f_to_save = "books/static/books/image_"+p.slug+".jpg"
                try:
                    data = urlopen(
                        "https://www.googleapis.com/books/v1/volumes?q=title:"+quote(p.title), data=None, timeout=5)
                    p_data = loads(data.read())[
                        "items"][0]["volumeInfo"]
                    if not "imageLinks" in p_data:
                        print("No image could be scraped for book '%s'" %
                              p.title)
                        return
                    retrieve(p_data["imageLinks"]["thumbnail"], f_to_save)
                    p.img = "https://everylibrary.co/static/"+f_to_save
                    p.save()
                    print("Scraped image for '%s', saved image at" %
                          p.title, f_to_save)
                except HTTPError as e:
                    print("Error:", e)
        except KeyboardInterrupt:
            print("\nQuitting...")
            return
