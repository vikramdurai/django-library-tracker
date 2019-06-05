from django.core.management.base import BaseCommand, CommandError
# from django.utils import timezone
# from django.utils.dateparse import parse_datetime
from datetime import datetime
from books.models import *
import csv


def makeborrowers():
    # This code generates all addresses in GoodEarth Malhar
    # Addresses are structured like so:
    # F10, Mosaic, GoodEarth Malhar
    # ^    ^ project/cluster ^ development community
    # house number + block
    # TODO: implement this in library code itself
    blocks = ["A","B","C","D","E","F"]
    cluster = ["Mosaic", "Footprints", "Patterns", "Resonance", "Terraces"]
    house_no = range(1, 12)
    for c in cluster:
        for b in blocks:
            for h in house_no:
                name = b+str(h)+", "+c
                if Borrower.objects.filter(name=name).exists():
                    continue
                a = Borrower(name=name, slug="")
                a.save()

# parse addresses in register
def parseaddrs(x):
    # Good Earth Malhar's address data is in the format
    # of MO-F10 whereas we want it as F10, Mosaic
    cluster_map = {
        "MO":"Mosaic",
        "RE":"Resonance",
        "FP":"Footprints",
        "PA":"Patterns",
        "TE":"Terraces",
        "OR": "Unknown"
    }
    cluster = cluster_map[x[0:2]]
    block = x[3]
    # sometimes Terraces has 3-digit house numbers
    house_no = int(x[4:])
    name = block+str(house_no)+", "+cluster
    a = Borrower.objects.filter(name=name)
    if a.exists():
        return a.first()
    a = Borrower(name=name, slug="")
    a.save()
    return a



def i_books(csv_filename):
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
            p = Publication.objects.filter(code=i[6]).all()
            if p:
                # There's an existing copy of the book
                # in the library
                p = p[0]

                _dt = None
                dt = None
                try:
                    _dt = datetime.strptime(i[9], "%d-%b-%Y")
                except ValueError as e:
                    if not i[9] == "":
                        _dt = datetime.strptime('0'+i[9], "%d-%B-%Y")
                if _dt:
                    dt = _dt.date()
                pass
                b = Book(publication=p, library=Library.objects.get(name='Good Earth Malhar Library'), acc=i[7], date_added=dt)
                b.save()
            else:
                # This is a completely new book
                # Create the book using the data, and save it
                p = Publication(sno=i[1], author=a, title=i[3], price=(lambda x: int(x) if x else 0)(i[4]),
                                genre=i[5], code=i[6],
                                available_goodreads=goodreads_converter(
                                    i[8]))
                p.save()
                print(i[9])
                _dt = None
                dt = None
                try:
                    _dt = datetime.strptime(i[9], "%d-%b-%Y")
                except ValueError as e:
                    if not i[9] == "":
                        _dt = datetime.strptime('0'+i[9], "%d-%B-%Y")
                if _dt:
                    dt = _dt.date()
                pass
                b = Book(publication=p, library=Library.objects.get(name='Good Earth Malhar Library'), acc=i[7], date_added=dt)
                b.save()
            b.save()


def i_register(csv_filename):
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
            borrower_abbreviated = i[3]
            borrower = parseaddrs(borrower_abbreviated)
            book = Book.objects.filter(acc=i[2])
            if not book.exists():
                # this book don't even exist
                continue
            else:
                book = book.all()[0]
            _dt = None
            dt = None 
            try:
                _dt = datetime.strptime(i[0], "%d-%b-%Y")
            except ValueError as e:
                if not i[0] == "":
                    try:
                        _dt = datetime.strptime('0'+i[0], "%d-%B-%Y")
                    except ValueError as e:
                        _dt = datetime.strptime(i[0], "%d-%b-%y")
            if _dt:
                dt = _dt.date()
            pass
            r = RegisterEntry(library=Library.objects.get(id=1), borrower=borrower, date=dt,
                              action="borrow", book=book)
            r.save()


class Command(BaseCommand):
    help = "Imports CSV data from a library spreadsheet into the model"

    def add_arguments(self, parser):
        parser.add_argument("--all",
                            help="Import books and register combined", action="store_true")
        parser.add_argument("--input", type=str,
                            help="What kind of action import should do.")
        parser.add_argument("--file", type=str,
                            help="CSV file input to import")

    def handle(self, *args, **options):
        if options["all"]:
            csv_files = [
                "spreadsheets/Toddler.csv",
                "spreadsheets/Fiction-Adult.csv",
                "spreadsheets/Nonfiction-Adult.csv",
                "spreadsheets/Young-Adult.csv"
            ]
            register = "spreadsheets/register.csv"
            for i in csv_files:
                i_books(i)
            print("Loaded books")
            makeborrowers()
            print("Loaded borrowers")
            i_register(register)
            print("Loaded register")

        csv_filename = options["file"]
        if options["input"] == "books":
            i_books(csv_filename)
            print("Loaded books")

        elif options["input"] == "register":
            i_register(csv_filename)
            print("Loaded register")
        
        elif options["input"] == "borrowers":
            makeborrowers()
            print("Loaded borrowers")
