from django.db import models
from django.template.defaultfilters import slugify
from django.conf import settings
from django.contrib import admin
from datetime import timedelta
# Create your models here.


class Author(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class Publication(models.Model):
    # Publication represents a single book title
    # in the library
    sno = models.IntegerField(null=True)
    title = models.CharField(max_length=200)
    date_added = models.DateTimeField("Date added to the library", null=True)
    author = models.ForeignKey(
        Author, on_delete=models.PROTECT, related_name="books")
    code = models.CharField(max_length=100, null=True)
    available_goodreads = models.BooleanField(default=False)
    genre = models.CharField(max_length=200, null=True)
    price = models.IntegerField(null=True)
    copies = models.IntegerField(default=0)
    slug = models.SlugField(max_length=255)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Publication, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class Book(models.Model):
    publication = models.ForeignKey(Publication, null=True)
    acc = models.CharField(max_length=200, null=True)


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


class ExtendLog(models.Model):
    current_returndate = models.DateTimeField(null=True)
    original_returndate = models.DateTimeField(null=True)


class RegisterEntry(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT, null=True)
    most_recent_extendlog = models.ForeignKey(ExtendLog, null=True)
    date = models.DateTimeField(null=True)
    action = models.CharField(max_length=6)
    borrower = models.ForeignKey(Borrower, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            # create a new Log here
            # I'm just hardcoding the initial return date here
            # which is 20
            e = ExtendLog(current_returndate=self.date + timedelta(20),
                          original_returndate=self.date + timedelta(20))
            e.save()
        super(RegisterEntry, self).save(*args, **kwargs)
