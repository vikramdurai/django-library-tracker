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

def date_processor(x):
    book_date = None
    try:
        book_date = datetime.strptime(x, "%d-%b-%Y")
    except ValueError: # sometimes the format of the date is wrong
        if x.split()[0][0] == "0" or len(x.split()[0]) >= 2: # it doesn't have to do with the day field
            date_construct = x.split("-")
            if len(date_construct[1]) != 3:
                # the month field is not abbreviated
                # this converts the string "07-April-2018" into "07-Apr-2018"
                new_str = date_construct[0] + "-" + date_construct[1][:3] + "-" + date_construct[2]
                book_date = datetime.strptime(new_str, "%d-%b-%Y")
        else: # wrong day field
            # usually fixed by added a zero
            book_date = datetime.strptime('0'+row[9], "%d-%B-%Y")
    return book_date


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
                _, created = Series.objects.get_or_create(num=int(data[0]), desc=" ".join(data[3:]))
                if created:
                    print("created new series:", str(s))
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

            def get_code_and_sanitize(r):
                return r.split()[0].lstrip('"').rstrip('"')
            
            g, created = Genre.objects.get_or_create(name=row[2], code=get_code_and_sanitize(row[0]), series=current_series)
            if created:
                print("created new genre:", g.code, g.name, "series:", g.series.desc)

def i_authors(csv_filename):
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)

        for row in rows:
            a, ok = Author.objects.get_or_create(name=row[2])

def i_comics(csv_filename):
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        # skip useless rows
        next(rows)
        next(rows)
        next(rows)

        for row in rows:
            # row structure for comics:
            # row[0] -> empty
            # row[1] -> s. no
            # row[2] -> title
            # row[3] -> price
            # row[4] -> author
            # row[5] -> code
            # row[6] -> acc #
            # row[8] -> d.o.a

            # check if blank
            if not row[2]:
                continue

            a, created = Author.objects.get_or_create(name=row[4])
            if created:
                print("created new author for comics:", a.name)

            _, created = Publication.objects.get_or_create(
                sno=row[1],
                title=row[2],
                price=row[3],
                author=a)

def i_magazines(csv_filename):
    print("inside i_mags")
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        # skip useless rows
        next(rows)
        next(rows)
        next(rows)

        for row in rows:
            # row structure for comics:
            # row[0] -> empty
            # row[1] -> s. no
            # row[2] -> title
            # row[3] -> price
            # row[4] -> code
            # row[5] -> acc #
            # row[7] -> d.o.a (blank)

            # check if blank
            print("inside for loop")
            if not row[2]:
                continue
            # magazines don't have an author
            a, created = Author.objects.get_or_create(name="None")
            if created:
                print("created new author for magazines:", a.name)

            _, created = Publication.objects.get_or_create(
                sno=row[1],
                title=row[2],
                price=int_or_zero(row[3]),
                author=a)
            if created:
                print("created a magazine")


def i_publications(csv_filename):
    ### dont use book codes

    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        # skip the three non-useful rows
        next(rows)
        next(rows)
        next(rows)


        # the rows in the comics sheet and the magazine sheet are inconsistent
        # with the rows of every other
        test_if_special = list(rows)[0]
        # the comics have "C" at the start of their book codes
        if test_if_special[5].startswith("C"):
            i_comics(csv_filename)
            return
        # whereas the magazines have "EM"
        if test_if_special[4].startswith("EM"):
            print("inside if")
            i_magazines(csv_filename)
            return

        # iterate over every row, and
        # do a get or create for Publications model
        for row in rows:

            # how each row is constructed normally:
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

            _, created = Publication.objects.get_or_create(
                sno=row[1],
                title=row[3],
                price=int_or_zero(row[4]),
                author=Author.objects.get(name=row[2]),
                available_goodreads=yn_converter(row[8]),
                genre=row[5],
                genre_type=Genre.objects.filter(name=" ".join(row[5].split()[1:])).first())
            if created:
                print("created new publication:", _.title)

def update_comics(csv_filename):
    # old and new book code updating
    print("im in")
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        print("ok")
        for row in rows:
            if not row[2]:
                continue

            c, created = Genre.objects.get_or_create(code="0.00", name="COMICS", series=Series.objects.get(num=0))
            if created:
                print("comics genre did not exist, created..")
                
            a = Author.objects.get(name=row[4])
            print("got author")
            p = Publication.objects.get(
                sno=row[1],
                title=row[2],
                price=row[3],
                author=a)
            print("got publication")
            p.genre_type = c
            p.genre = str(c)
            print("set genre type", str(c))
            p.code = row[5]
            p.save()

def update_magazines(csv_filename):
    # old and new book code updating
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        
        for row in rows:
            if not row[2]:
                continue

            c, created = Genre.objects.get_or_create(code="2.00", name="MAGAZINES", series=Series.objects.get(num=200))
            if created:
                print("comics genre did not exist, created..")

            # magazines don't have an author
            a = Author.objects.get(name="None")
            p = Publication.objects.get(
                sno=row[1],
                title=row[2],
                price=int_or_zero(row[3]),
                author=a)
            p.genre = str(c)
            p.genre_type = c
            p.code = row[5]
            p.save()


def update_publications(csv_filename):
    # old and new book code updating
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        
        test_if_special = list(rows)[0]
        # comics book codes start with "C"
        if test_if_special[5].startswith("C"):
            print("comics")
            update_comics(csv_filename)
            return
        # whereas the magazines have "EM"
        if test_if_special[4].startswith("EM"):
            update_magazines(csv_filename)
            return

        for row in rows:
            if not row[3]:
                continue
            print(row)
            p = Publication.objects.get(
                sno=row[1],
                title=row[3],
                price=int_or_zero(row[4]),
                available_goodreads=yn_converter(row[8]),
                genre=row[5])
            p.genre_type = Genre.objects.get(code=row[5].split()[0])
            p.code = row[6]
            p.save()

def i_books(csv_filename, library):
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)

        test_if_special = list(rows)[0]
        # comics book codes start with "C"
        if test_if_special[5].startswith("C"):
            books_comics(csv_filename, library)
            return
        # whereas the magazines have "EM"
        if test_if_special[4].startswith("EM"):
            books_magazines(csv_filename, library)
            return

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
                genre=row[5])
                # genre_type=Genre.objects.filter(name=row[5].split()[1:]).first())
            except Exception as e:
                print("i_books: Unexpected error:", str(e))
                continue
            
            # create the dates

            if not row[9]: # the date field is empty
                 print("i_books: found empty date field for book #" + row[7] + ", proceeding to create")
                 b = Book.objects.get_or_create(publication=pub, library=Library.objects.get(name=library))
                 continue

            b = Book.objects.get_or_create(publication=pub, library=Library.objects.get(name=library), date_added=date_processor(row[9]).date())

def books_comics(csv_filename, library):
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        
        for row in rows:
            # row[0] -> empty
            # row[1] -> s. no
            # row[2] -> title
            # row[3] -> price
            # row[4] -> code
            # row[5] -> acc #
            # row[8] -> d.o.a (blank)
            if not row[2]:
                continue

            c, created = Genre.objects.get_or_create(code="0.00", name="COMICS", series=Series.objects.get(num=0))
            if created:
                print("comics genre did not exist, created..")

            # get parent publication
            pub = None
            try:
                pub = Publication.objects.get(
                sno=row[1],
                title=row[2])
            except Exception as e:
                print("books_comics: Unexpected error:", str(e), "row:", row)
                continue
            
            # create the dates

            if not row[8]: # the date field is empty
                 print("books_comics: found empty date field for book #" + row[7] + ", proceeding to create")
                 b = Book.objects.get_or_create(publication=pub, library=Library.objects.get(name=library))
                 continue
                
            b = Book.objects.get_or_create(publication=pub, library=Library.objects.get(name=library), date_added=date_processor(row[8]).date())

def books_magazines(csv_filename, library):
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        
        for row in rows:
            # row[0] -> empty
            # row[1] -> s. no
            # row[2] -> title
            # row[3] -> price
            # row[4] -> code
            # row[5] -> acc #
            # row[7] -> d.o.a (blank)
            if not row[2]:
                continue

            m, created = Genre.objects.get_or_create(code="2.00", name="MAGAZINES", series=Series.objects.get(num=200))
            if created:
                print("magazines genre did not exist, created..")

            # get parent publication
            pub = None
            try:
                pub = Publication.objects.get(
                sno=row[1],
                title=row[2])
            except Exception as e:
                print("books_magazines: Unexpected error:", str(e))
                continue
            
            # create the dates

            if not row[7]: # the date field is empty
                 print("books_magazines: found empty date field for book #" + row[5] + ", proceeding to create")
                 b = Book.objects.get_or_create(publication=pub, library=Library.objects.get(name=library))
                 continue
                
            b = Book.objects.get_or_create(publication=pub, library=Library.objects.get(name=library), date_added=date_processor(row[7]).date())

def update_comics_books(csv_filename):
    # old and new book acc updating
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        # row[0] -> empty
            # row[1] -> s. no
            # row[2] -> title
            # row[3] -> price
            # row[4] -> code
            # row[5] -> acc #
            # row[8] -> d.o.a (blank)
        for row in rows:
            if not row[2]:
                continue
            c, created = Genre.objects.get_or_create(code="0.00", name="COMICS", series=Series.objects.get(num=0))
            if created:
                print("comics genre did not exist, created..")
            # get parent publication
            pub = None
            try:
                pub = Publication.objects.get(
                sno=row[1],
                title=row[2])
            except Exception as e:
                print("update_comics: Unexpected error:", str(e), "row:", row)
                continue
            books = Book.objects.filter(publication=pub).all()
            for each in books:
                each.acc = row[5]
                each.save()

def update_magazines_books(csv_filename):
    # old and new book acc updating
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        # row[0] -> empty
            # row[1] -> s. no
            # row[2] -> title
            # row[3] -> price
            # row[4] -> code
            # row[5] -> acc #
            # row[7] -> d.o.a (blank)
        for row in rows:
            if not row[2]:
                continue
            m, created = Genre.objects.get_or_create(code="2.00", name="MAGAZINES", series=Series.objects.get(num=200))
            if created:
                print("magazines genre did not exist, created..")
            # get parent publication
            pub = None
            try:
                pub = Publication.objects.get(
                sno=row[1],
                title=row[2],
                price=int_or_zero(row[3]))
            except Exception as e:
                print("update_magazines: Unexpected error:", str(e))
                continue
            books = Book.objects.filter(publication=pub).all()
            for each in books:
                each.acc = row[5]
                each.save()

def update_books(csv_filename):
    # old and new book acc updating
    with open(csv_filename, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")
        next(rows)
        next(rows)
        next(rows)
        test_if_special = list(rows)[0]
        # comics book codes start with "C"
        if test_if_special[5].startswith("C"):
            update_comics_books(csv_filename)
            return
        # whereas the magazines have "EM"
        if test_if_special[4].startswith("EM"):
            update_magazines_books(csv_filename)
            return

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
                genre=row[5])
                # genre_type=Genre.objects.filter(name=row[5].split()[1:]).first())
            except Exception as e:
                print("i_books: Unexpected error:", str(e))
                continue
            books = Book.objects.filter(publication=pub).all()
            for each in books:
                each.acc = row[7]
                each.save()
            
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
            print("Loaded books")
        
        if options["input"] == "update_books":
            update_books(csv_filename)
            print("Updated books")

        elif options["input"] == "register":
            i_register(csv_filename)
            print("Loaded register")
        
        elif options["input"] == "borrowers":
            makeborrowers()
            print("Loaded borrowers")
