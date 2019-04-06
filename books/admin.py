from django.contrib import admin

from .models import Author, Publication, Book, RegisterEntry, Borrower, UserStaff


class PublicationAdmin(admin.ModelAdmin):
    list_display = ("sno", "title", "date_added", "author",
                    "code", "available_goodreads", "genre", "price")


class BookAdmin(admin.ModelAdmin):
    list_display = ("publication", "acc")


class RegisterEntryAdmin(admin.ModelAdmin):
    list_display = ("book", "action", "date", "borrower", "user")


admin.site.register(Author)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(UserStaff)
admin.site.register(RegisterEntry, RegisterEntryAdmin)
admin.site.register(Borrower)
