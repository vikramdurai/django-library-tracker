from django.core.management.base import BaseCommand, CommandError
from books.models import *
from datetime import datetime
import xlsxwriter


def export_from_series(series_code):
    try:
        s = Series.objects.get(num=series_code)
    except Series.DoesNotExist:
        print("The requested series does not exist")
        return None, True
    genres = s.genres.all()
    pubs = []
    for g in genres:
        for p in g.publications.all():
            pubs.append(p)

    what_to_write = [
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, s.desc.upper(), None, None, None, None, None, None, None],
        ["S.NO", "AUTHOR", "TITLE", "PRICE", "GENRE", "BOOK CODE", "ACC #", "AVAILABILITY ON GOODREADS", "DATE OF ADDITION"]]
    for pub in pubs:
        what_to_write.append([pub.sno, pub.author.name, pub.title, pub.price, pub.genre,
                              pub.code, pub.editions.all().first().acc, pub.available_goodreads, pub.editions.all().first().date_added])
    return what_to_write, True


def export_register():
    # create the overdue register
    header = "Books In Circulation as of " + \
        datetime.strftime(datetime.today(), "%d %B %Y")
    what_to_write = [
        [header, None, None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None,
            "Kindly return/renew at the earliest. The library is open Tue-Fri from 5 pm to 6.30 pm and Saturday 10.30 am to 12 noon at Courtyard Koota. Regards, Anaswara"],
        ["S.No.", "Acc #", "Borrower", "Due date", "Remarks", "Name of person", "Phone number", "Name of book",
            "# of overdue books", "Whatsapp message line 1", "Whatsapp message line 2", "Whatsapp message line 3"]
    ]
    entries = RegisterEntry.get_all_borrowed_entries()
    for entry in entries:
        book = entry.book
        borrower = entry.borrower
        pub = book.publication
        num_borrowed = len(RegisterEntry.get_all_under_borrower(borrower))
        w1 = None
        w2 = None
        if num_borrowed > 1:
            w1 = "Hi " + borrower.person + ", Greetings from the Malhar Library. As per our records, you have " + \
                str(num_borrowed) + " overdue books with you. "
            w2 = "The name of the books are"
        else:
            w1 = "Hi " + borrower.person + ", Greetings from the Malhar Library. As per our records, you have " + \
                str(num_borrowed) + " overdue book with you. "
            w2 = "The name of the book is '" + pub.title+"'"

        # create borrower.person, borrower.pn
        what_to_write.append([pub.sno, book.acc, borrower.abbrev(
        ), entry.date, None, borrower.person, borrower.pn, pub.title, num_borrowed, w1, w2, None])
    return what_to_write


def export_key():
    all_series = Series.objects.all().exclude(num=200)  # exclude magazines
    what_to_write = [
        ["CATALOGUE KEY # of books (excluding magazines)", len(
            Publication.objects.all())],
    ]
    for s in all_series:
        sgenres = s.genres.all()
        spubs = []
        for g in sgenres:
            spubs.extend(g.publications.all())
        what_to_write.append(["%s SERIES - %s" %
                              (s.num, s.desc.upper()), len(spubs)])
        for g in sgenres:
            what_to_write.append(
                [g.code, g.name.upper(), len(g.publications.all())])

    return what_to_write


class Command(BaseCommand):
    help = "Exports data from the model into a .xlsx file"

    def add_arguments(self, parser):
        parser.add_argument("--series", type=str,
                            help="Codes for series to import (as in '700 800' & the like)")
        parser.add_argument("--register", help="Flag to create the register")

    def handle(self, *args, **options):
        if not options["register"]:
            nseries_names = options["series"].split()
            workbook = xlsxwriter.Workbook("out.xlsx")
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
        else:
            workbook = xlsxwriter.Workbook("out.xlsx")
            w = workbook.add_worksheet(
                "overdue-"+datetime.strftime(datetime.today(), "%b'%y").lower())  # overdue-nov'19
            data = export_register()
            for row_num, columns in enumerate(data):
                for col_num, cell_data in enumerate(columns):
                    w.write(row_num, col_num, cell_data)
            print("Done.")
            workbook.close()
