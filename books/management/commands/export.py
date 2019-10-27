from django.core.management.base import BaseCommand, CommandError
from books.models import *
from csv import reader, writer
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

    def handle(self, *args, **options):
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
