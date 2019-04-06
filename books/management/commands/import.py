from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from books.models import *
import csv


class Command(BaseCommand):
    help = "Imports CSV data from a library spreadsheet into the model"

    def add_arguments(self, parser):
        parser.add_argument("--input", type=str,
                            help="What kind of action import should do.")
        parser.add_argument("--file", type=str,
                            help="CSV file input to import")

    def handle(self, *args, **options):
        csv_filename = options["file"]
        if options["input"] == "books":
            with open(csv_filename, newline="") as csv_file:
                x = csv.reader(csv_file, delimiter=",")
                # This code analyzes the data from the CSV
                # and converts it into a format suitable for the
                # book model in models.Book.
                # Here is how I do the conversion. Note that
                # with some data from Malhar Library the spreadsheets
                # are ordered differently:
                # i[0] -> nothing (may vary with some libraries)
                # i[1] -> s.no (may vary with some libraries)
                # i[2] -> author/publisher
                # i[3] -> title
                # i[4] -> price (may vary with some libraries)
                # i[5] -> genre
                # i[6] -> book code (may vary with some libraries)
                # i[7] -> accession number (may vary with some libraries)
                # i[8] -> availabilty on goodreads (may vary with some libraries)
                # i[9] -> date of addition

                # skip the first three rows
                # they are not valid fields
                next(x)
                next(x)
                next(x)
                for i in x:
                    # is this an empty cell?
                    if not i[3]:
                        continue
                    # Check if the author is already in the
                    # database. If not, create an entry for them.
                    a = None
                    if not list(Author.objects.filter(name=i[2])):
                        a = Author(name=i[2])
                        a.save()
                    a = Author.objects.get(name=i[2])
                    # In the spreadsheet, the available_on_goodreads value
                    # is a string ("Y" or "") instead of True and False.
                    # This function converts "Y" and company into True/False.

                    def goodreads_converter(x):
                        if x == "Y":
                            return True
                        return False
                    p = Publication.objects.filter(code=i[6]).all()[0]
                    if p:
                        # There's an existing copy of the book
                        # in the library
                        b = Book(publication=p, acc=i[7])
                        p.copies += 1
                        b.save()
                        p.save()
                    else:
                        # This is a completely new book
                        # Create the book using the data, and save it
                        p = Publication(sno=i[1], author=a, title=i[3], price=(lambda x: int(x) if x else 0)(i[4]),
                                        genre=i[5], code=i[6],
                                        available_goodreads=goodreads_converter(
                                            i[8]),
                                        date_added=parse_datetime(i[9]))
                        p.save()
                        b = Book(publication=p, acc=i[7])
                        p.copies += 1
                        b.save()
                        p.save()
                    b.save()
                print("Loaded books")

        elif options["input"] == "register":
            with open(csv_filename, newline="") as csv_file:
                x = csv.reader(csv_file, delimiter=",")
                # Skip the first line because it's useless
                next(x)
                # This code analyzes data from another spreadsheet
                # (namely, the book log of when a particular book
                # was borrowed/returned) and converts it into an
                # entry in models.RegisterEntry
                # Here is how I do the conversion (at least with Malhar
                # Library):
                # i[0] -> date borrowed
                # i[1] -> date due
                # i[2] -> accession number of the book borrowed
                # i[3] -> borrower's house
                # i[4] -> date returned (if given)
                # Bear in mind that this code was written to work
                # with Malhar Library's spreadsheets.
                for i in x:
                    # Check if the borrower is already in the
                    # database. If not, create an entry for them.
                    borrower = None
                    if not list(Borrower.objects.filter(name=i[3])):
                        borrower = Borrower(name=i[3])
                        borrower.save()
                    borrower = Borrower.objects.get(name=i[3])
                    book = Book.objects.filter(acc=i[2])
                    if list(book) == []:
                        # this book don't even exist
                        book = None
                        continue
                    else:
                        book = book.all()[0]
                    r = RegisterEntry(borrower=borrower, date=parse_datetime(i[0]),
                                      action="borrow", book=book)
                    r.save()
