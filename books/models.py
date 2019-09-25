from django.db import models
from django.template.defaultfilters import slugify
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils import timezone
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

class Series(models.Model):
    num = models.IntegerField(default=0)
    desc = models.CharField(max_length=100)

    def __str__(self):
        return "%s %s" % (self.num, self.desc.lower().title())


class Genre(models.Model):
    name = models.CharField(null=True, max_length=200)
    code = models.CharField(null=True, max_length=50)
    series = models.ForeignKey(Series, on_delete=models.PROTECT, related_name="genres", null=True)

    def as_list(self):
        return [self.code, self.name]

class Publication(models.Model):
    # Publication represents a single book title
    # in the library
    sno = models.IntegerField(null=True)
    title = models.CharField(max_length=200)
    author = models.ForeignKey(
        Author, on_delete=models.PROTECT, related_name="books")
    img = models.URLField(null=True)
    code = models.CharField(max_length=100, null=True, blank=True)
    available_goodreads = models.BooleanField(default=False)
    genre_type = models.ForeignKey(Genre, null=True, on_delete=models.SET_NULL, related_name="publications")
    genre = models.CharField(max_length=200, null=True)
    price = models.IntegerField(null=True)
    slug = models.SlugField(max_length=255)
    isbn = models.CharField(max_length=100, null=True)
    # image = models.ImageField(null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Publication, self).save(*args, **kwargs)

    def get_copies(self):
        return Book.objects.filter(publication=self)
    
    @staticmethod
    def get_all_with_images():
        return Publication.objects.all().exclude(img=None).all()

    def __str__(self):
        return self.title

class Book(models.Model):
    publication = models.ForeignKey(Publication, null=True)
    date_added = models.DateField("Date added to the library", null=True)
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


class UserJoinRequest(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, null=True, on_delete=models.PROTECT)
    borrower = models.ForeignKey(
        Borrower, null=True, on_delete=models.SET_NULL)
    approved = models.BooleanField(default=False)


class UserMember(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, null=True, on_delete=models.PROTECT)
    borrower = models.ForeignKey(
        Borrower, null=True, on_delete=models.SET_NULL)


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
    date = models.DateField(null=True)
    action = models.CharField(max_length=6)
    library = models.ForeignKey(Library, null=True, on_delete=models.PROTECT)
    borrower = models.ForeignKey(Borrower, null=True)
    user = models.ForeignKey(UserMember, null=True)

    def save(self, *args, **kwargs):
        if not self.id and self.action == "borrow":
            # create a new Log here
            # I'm just hardcoding the initial return date here
            # which is 20
            e = ExtendLog(entry=self, new_returndate=timezone.now() + timedelta(self.library.default),
                          returndate=timezone.now() + timedelta(self.library.default))
            super(RegisterEntry, self).save(*args, **kwargs)
            e.save()
            self.most_recent_extendlog = e
        super(RegisterEntry, self).save(*args, **kwargs)

    def __str__(self):
        return "Action: %s Book: %s Borrower: %s" % (self.action, self.book, self.borrower)

    @staticmethod
    def get_all_borrowed_entries():
        all_borrowed_entries = RegisterEntry.objects.filter(action="borrow")
        all_returned_entries = [
            i.book for i in RegisterEntry.objects.filter(action="return")]
        borrowed_entries_that_are_not_in_returned_entries = all_borrowed_entries.exclude(
            book__in=all_returned_entries)
        return borrowed_entries_that_are_not_in_returned_entries

    @staticmethod
    def is_borrowed(b):
        # this checks to see if the book 'b' is among
        # the currently borrowed books
        if RegisterEntry.get_all_borrowed_entries().filter(book=b).exists():
            return True
        return False
