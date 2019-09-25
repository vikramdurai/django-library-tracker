from django.core.management.base import BaseCommand, CommandError
# from django.utils import timezone
# from django.utils.dateparse import parse_datetime
from datetime import datetime
from books.models import *
import csv



def accify(g, existing):
    return g.series.num[0]+"."+existing[1:]

def create_book_code(author, genre_num, count):
    return str(genre_num) + "." + author.name[:2].upper() + str(count+1)

def int_or_zero(x):
    if x:
        return int(x)
    return 0

# convert Y/N to True and False
def yn_converter(x):
    if x == "Y":
        return True
    elif x == "N":
        return False
    return False


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

def i_series(csv_filename):
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        # skip first two rows, they're useless
        next(rows)
        next(rows)

        # iterate over every row and check
        # if it is either a series or a genre
        # we do this by checking if it has the
        # word 'series' in the second column
        for row in rows:
            
            # check if it's a series
            if "SERIES" in row[1]:
                data = row[1].split()
                # create the series
                s, created = Series.objects.get_or_create(num=int(data[0]), desc=" ".join(data[3:]))
                continue


def i_genres(csv_filename):
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        current_series = None

        for row in rows:
            # row map:
            # row[0] - the full name, e.g "1.01 English Books for Issue"
            # row[1] - the ACC #, e.g "1.01"
            # row[2] - the description, e.g "English Books for Issue"
            # row[3] - the number of books in that genre, e.g "81"

            # skip if series
            if "SERIES" in row[1]:
                current_series = Series.objects.filter(num=row[1].split()[0]).first()
                print("current series is now", current_series.desc)
                continue

            g, ok = Genre.objects.get_or_create(name=row[2], code=row[1], series=current_series)

def i_authors(csv_filename):
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)

        for row in rows:
            a, ok = Author.objects.get_or_create(name=row[2])

def i_publications(csv_filename):
    ### dont use book codes

    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        # skip the three non-useful rows
        next(rows)
        next(rows)
        next(rows)

        # iterate over every row, and
        # do a get or create for Publications model
        for row in rows:
            # how each row is constructed:
            # row[0] -> nothing
            # row[1] -> s.no
            # row[2] -> author/publisher
            # row[3] -> title
            # row[4] -> price
            # row[5] -> genre
            # row[6] -> book code
            # row[7] -> accession number
            # row[8] -> availabilty on goodreads 
            # row[9] -> date of addition

            if not row[3]: # blank cell
                continue
            pub, ok = Publication.objects.get_or_create(
                sno=row[1],
                title=row[3],
                price=int_or_zero(row[4]),
                author=Author.objects.get(name=row[2]),
                available_goodreads=yn_converter(row[8]),
                genre=row[5],
                genre_type=Genre.objects.filter(name=row[5].split()[1:]).first())


def update_publications(csv_filename):
    # old and new book code updating
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        
        for row in rows:
            if not row[3]:
                continue
            p = Publication.objects.get(
                sno=row[1],
                title=row[3],
                price=int_or_zero(row[4]),
                available_goodreads=yn_converter(row[8]),
                genre=row[5],
                genre_type=Genre.objects.filter(name=row[5].split()[1:]).first())
            p.code = row[6]
            p.save()

def i_books(csv_filename, library):
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        
        for row in rows:
            if not row[3]:
                continue

            # get parent publication
            pub = None
            try:
                pub = Publication.objects.get(
                sno=row[1],
                title=row[3],
                price=int_or_zero(row[4]),
                available_goodreads=yn_converter(row[8]),
                genre=row[5],
                genre_type=Genre.objects.filter(name=row[5].split()[1:]).first())
            except Exception as e:
                print("i_books: Unexpected error:", str(e))
                continue
            
            # create the dates

            if not row[9]: # the date field is empty
                 print("i_books: found empty date field for book #" + row[7] + ", proceeding to create")
                 b = Book.objects.get_or_create(publication=pub, library=Library.objects.get(name=library))
                 continue

            book_date = None
            try:
                book_date = datetime.strptime(row[9], "%d-%b-%Y")
            except ValueError: # sometimes the format of the date is wrong
                if row[9].split()[0][0] == "0" or len(row[9].split()[0]) >= 2: # it doesn't have to do with the day field
                    date_construct = row[9].split("-")
                    if len(date_construct[1]) != 3:
                        # the month field is not abbreviated
                        # this converts the string "07-April-2018" into "07-Apr-2018"
                        new_str = date_construct[0] + "-" + date_construct[1][:3] + "-" + date_construct[2]
                        book_date = datetime.strptime(new_str, "%d-%b-%Y")

                else: # wrong day field
                    # usually fixed by added a zero
                    book_date = datetime.strptime('0'+row[9], "%d-%B-%Y")
            
            b = Book.objects.get_or_create(publication=pub, library=Library.objects.get(name=library), date_added=book_date.date())

def update_books(csv_filename):
    # old and new book acc updating
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        
        for row in rows:
            if not row[3]:
                continue
            # get parent publication
            pub = None
            try:
                pub = Publication.objects.get(
                sno=row[1],
                title=row[3],
                price=int_or_zero(row[4]),
                available_goodreads=yn_converter(row[8]),
                genre=row[5],
                genre_type=Genre.objects.filter(name=row[5].split()[1:]).first())
            except Exception as e:
                print("i_books: Unexpected error:", str(e))
                continue
            books = Book.objects.filter(publication=pub).all()
            for each in books:
                each.acc = row[7]
                each.save()
            
# def i_books(csv_filename):
#     with open(csv_filename, newline="") as csv_file:
#         x = csv.reader(csv_file, delimiter=",")
#         # This code analyzes the data from the CSV
#         # and converts it into a format suitable for the
#         # book model in models.Book.
#         # Here is how I do the conversion. Note that
#         # with some data from Malhar Library the spreadsheets
#         # are ordered differently:
#         # i[0] -> nothing (may vary with some libraries)
#         # i[1] -> s.no (may vary with some libraries)
#         # i[2] -> author/publisher
#         # i[3] -> title
#         # i[4] -> price (may vary with some libraries)
#         # i[5] -> genre
#         # i[6] -> book code (may vary with some libraries)
#         # i[7] -> accession number (may vary with some libraries)
#         # i[8] -> availabilty on goodreads (may vary with some libraries)
#         # i[9] -> date of addition

#         # skip the first three rows
#         # they are not valid fields
#         next(x)
#         next(x)
#         next(x)
#         for i in x:
#             # is this an empty cell?
#             if not i[3]:
#                 continue
#             # Check if the author is already in the
#             # database. If not, create an entry for them.
#             a = None
#             if not list(Author.objects.filter(name=i[2])):
#                 a = Author(name=i[2])
#                 a.save()
#             a = Author.objects.get(name=i[2])
#             # In the spreadsheet, the available_on_goodreads value
#             # is a string ("Y" or "") instead of True and False.
#             # This function converts "Y" and company into True/False.

#             def goodreads_converter(x):
#                 if x == "Y":
#                     return True
#                 return False
#             p = Publication.objects.filter(code=i[6]).all()
#             if p:
#                 # There's an existing copy of the book
#                 # in the library
#                 p = p[0]

#                 _dt = None
#                 dt = None
#                 try:
#                     _dt = datetime.strptime(i[9], "%d-%b-%Y")
#                 except ValueError as e:
#                     if not i[9] == "":
#                         _dt = datetime.strptime('0'+i[9], "%d-%B-%Y")
#                 if _dt:
#                     dt = _dt.date()
#                 pass
#                 b = Book(publication=p, library=Library.objects.get(name='Good Earth Malhar Library'), acc=i[7], date_added=dt)
#                 b.save()
#             else:
#                 # This is a completely new book
#                 # Create the book using the data, and save it
#                 p = None
#                 if i[5].startswith("C"):
#                     # this is a comic
#                     comics = Series.objects.get(num=100)
#                     genre_ = Genre.objects.filter(series=comics).first()
#                     count = len()
#                     Publication.objects.get_or_create(
#                         title=i[2],
#                         author=Author.objects.get_or_c(name=i[4]))
#                 elif i[6].startswith("EM"):
#                     # this is a magazine
#                 else:
#                     p = Publication(sno=i[1], author=a, title=i[3], price=(lambda x: int(x) if x else 0)(i[4]),
#                                     genre_type=Genre.objects.filter(name=i[5][4:], code=i[5][:3]).first(), genre=i[5],
#                                     available_goodreads=goodreads_converter(
#                                         i[8]))
#                 p.save()
#                 print(i[9])
#                 _dt = None
#                 dt = None
#                 try:
#                     _dt = datetime.strptime(i[9], "%d-%b-%Y")
#                 except ValueError as e:
#                     if not i[9] == "":
#                         _dt = datetime.strptime('0'+i[9], "%d-%B-%Y")
#                 if _dt:
#                     dt = _dt.date()
#                 pass
#                 b = Book(publication=p, library=Library.objects.get(name='Good Earth Malhar Library'), acc=i[7], date_added=dt)
#                 b.save()
#             b.save()


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
        # parser.add_argument("--all",
        #                     help="Import books and register combined", action="store_true")
        parser.add_argument("--input", type=str,
                            help="What kind of action import should do.")
        parser.add_argument("--file", type=str,
                            help="CSV file input to import")

    def handle(self, *args, **options):
        # if options["all"]:
        #     csv_files = [
        #         "spreadsheets/Sat_1492019-catalogue/ML_Catalogue.xlsx - 1_TODDLER.csv",
        #         "spreadsheets/Sat_1492019-catalogue/ML_Catalogue.xlsx - 7_YOUNG_ADULT.csv",
        #         "spreadsheets/Sat_1492019-catalogue/ML_Catalogue.xlsx - 6_YOUNG_READER.csv",
        #         "spreadsheets/Sat_1492019-catalogue/ML_Catalogue.xlsx - 7_YOUNG_ADULT.csv",
        #         "spreadsheets/Sat_1492019-catalogue/ML_Catalogue.xlsx - 8_FICTION_ADULT.csv",
        #         "spreadsheets/Sat_1492019-catalogue/ML_Catalogue.xlsx - 9_NONFICTION_ADULT.csv",
        #     ]
        #     register = "spreadsheets/register.csv"
        #     key = "spreadsheets/ready_key.csv"
            
        #     i_series(key)
        #     i_genres(key)
            
        #     for i in csv_files:    
        #         i_books(i)
            
        #     print("Loaded books")
        #     makeborrowers()
        #     print("Loaded borrowers")
        #     i_register(register)
        #     print("Loaded register")

        csv_filename = options["file"]

        if options["input"] == "series":
            i_series(csv_filename)
            print("Loaded series")

        if options["input"] == "genres":
            i_genres(csv_filename)
            print("Loaded genres")

        if options["input"] == "authors":
            i_authors(csv_filename)
            print("Loaded authors")
        
        if options["input"] == "publications":
            i_publications(csv_filename)
            print("Loaded publications")
        
        if options["input"] == "update_pubs":
            update_publications(csv_filename)
            print("Updated publications")
        
        if options["input"] == "books":
            i_books(csv_filename, "Good Earth Malhar Library")
            print("Loaded publications")
        
        if options["input"] == "update_books":
            update_books(csv_filename)
            print("Updated publications")

        elif options["input"] == "register":
            i_register(csv_filename)
            print("Loaded register")
        
        elif options["input"] == "borrowers":
            makeborrowers()
            print("Loaded borrowers")
