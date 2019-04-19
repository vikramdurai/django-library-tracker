from django.contrib import admin

from .models import Library, Author, Publication, Book, RegisterEntry, Borrower, UserStaff, UserMember, UserJoinRequest, ExtendLog


class PublicationAdmin(admin.ModelAdmin):
    list_display = ("sno", "title", "author",
                    "code", "available_goodreads", "genre", "price")


class BookAdmin(admin.ModelAdmin):
    list_display = ("publication", "date_added", "acc")


class RegisterEntryAdmin(admin.ModelAdmin):
    list_display = ("book", "action", "date", "borrower", "user")
    search_fields = ("book__publication__title", "action")


class ExtendLogAdmin(admin.ModelAdmin):
    list_display = ("new_returndate", "returndate")


class UserMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "library", "borrower")


class UserJoinRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "library", "borrower")


admin.site.register(Author)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(UserStaff)
admin.site.register(UserMember, UserMemberAdmin)
admin.site.register(UserJoinRequest, UserJoinRequestAdmin)
admin.site.register(RegisterEntry, RegisterEntryAdmin)
admin.site.register(ExtendLog, ExtendLogAdmin)
admin.site.register(Borrower)
admin.site.register(Library)
