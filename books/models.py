from django.db import models
from django.template.defaultfilters import slugify
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from datetime import timedelta
# Create your models here.


class Library(models.Model):
    name = models.CharField(max_length=255)
    default = models.IntegerField(default=20)

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class Publication(models.Model):
    # Publication represents a single book title
    # in the library
    sno = models.IntegerField(null=True)
    title = models.CharField(max_length=200)
    author = models.ForeignKey(
        Author, on_delete=models.PROTECT, related_name="books")
    code = models.CharField(max_length=100, null=True)
    available_goodreads = models.BooleanField(default=False)
    genre = models.CharField(max_length=200, null=True)
    price = models.IntegerField(null=True)
    slug = models.SlugField(max_length=255)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Publication, self).save(*args, **kwargs)

    def get_copies(self):
        return Book.objects.filter(publication=self)

    def __str__(self):
        return self.title


class Book(models.Model):
    publication = models.ForeignKey(Publication, null=True)
    date_added = models.DateTimeField("Date added to the library", null=True)
    acc = models.CharField(max_length=200, null=True)
    library = models.ForeignKey(Library, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return "Title: %s, ACC #: %s" % (self.publication.title, self.acc)


class Borrower(models.Model):
    # address = models.ForeignKey("Address", on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=40)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Borrower, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class UserMember(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, null=True, on_delete=models.PROTECT)

class UserStaff(models.Model):
    # UserStaff represents a staff account.
    # All we need is a link to the original user
    # so that when librarians (librarians, not admins)
    # sign into the app, the app can check for UserStaff
    # models that link to that user which is trying to sign
    # in. The on_delete is set to CASCADE because if a librarian
    # leaves the team, they'll have to delete their staff account.
    # By deleting that account and leaving the team, their
    # staff privileges need to be revoked, which is done automatically.
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             null=False, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.user.username


class ExtendLog(models.Model):
    entry = models.ForeignKey('RegisterEntry', null=True)
    new_returndate = models.DateTimeField(
        null=True)
    returndate = models.DateTimeField(
        null=True)

    def __str__(self):
        return "New return date: %s Old date: %s" % (self.new_returndate, self.returndate)


class RegisterEntry(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT, null=True)
    most_recent_extendlog = models.ForeignKey(ExtendLog, null=True)
    date = models.DateTimeField(null=True)
    action = models.CharField(max_length=6)
    library = models.ForeignKey(Library, null=True, on_delete=models.PROTECT)
    borrower = models.ForeignKey(Borrower, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    def save(self, *args, **kwargs):
        if not self.id and self.action == "borrow":
            # create a new Log here
            # I'm just hardcoding the initial return date here
            # which is 20
            e = ExtendLog(entry=self, new_returndate=self.library.default_returndate,
                          returndate=self.library.default_returndate)
            super(RegisterEntry, self).save(*args, **kwargs)
            e.save()
            self.most_recent_extendlog = e
        super(RegisterEntry, self).save(*args, **kwargs)

    def __str__(self):
        return "Action: %s Book: %s Borrower: %s" % (self.action, self.book, self.borrower)

    @staticmethod
    def get_all_borrowed_entries():
        x = RegisterEntry.objects.filter(action="borrow")
        y = [i.book for i in RegisterEntry.objects.filter(action="return")]
        z = x.exclude(book__in=y)
        return z
