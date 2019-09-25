from django.core.management.base import BaseCommand, CommandError
# from django.utils import timezone
# from django.utils.dateparse import parse_datetime
from datetime import datetime
from books.models import *
import csv

# parse addresses in register


def parseaddrs(x):
    # Good Earth Malhar's address data is in the format
    # of MO-F10 whereas we want it as F10, Mosaic
    cluster_map = {
        "MO": "Mosaic",
        "RE": "Resonance",
        "FP": "Footprints",
        "PA": "Patterns",
        "TE": "Terraces",
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


def i_book(f):
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
    tabs = ["8_FICTION_ADULT", "NONFICTION_ADULT",
            "YOUNG_ADULT", "YOUNG_READER", "TODDLER"]
    for w in tabs:
        row1 = ["", "", "", "", "", "", "", "", "", ""]
        row2 = ["", w]
        row3 = ["", "S.NO", "AUTHOR", "TITLE", "PRICE", "GENRE",
                "BOOK CODE", "ACC #", "AVAILABILITY ON GOODREADS", "DATE OF ADDITION"]
        rows = [row1, row2, row3]
        books_for_this_tab = Publication.objects.filter(genre__startswith=w[0])
        for i in books_for_this_tab:
            rows.append(["", i.sno, i.author.name, i.title, i.price,
                         i.genre, i.code, i.acc, i.available_goodreads, i.date])


class Command(BaseCommand):
    help = "Imports CSV data from a library spreadsheet into the model"

    def add_arguments(self, parser):
        parser.add_argument("--all",
                            help="Export books and register combined", action="store_true")
        parser.add_argument("--input", type=str,
                            help="What kind of action export should do.")
        parser.add_argument("--file", type=str,
                            help="CSV file to export into")

    def handle(self, *args, **options):
        if options["all"]:
            f = options["file"]
            reg = i_register(f)
            print("Exported register")
            bdb = i_book(f)
            print("Exported book")
