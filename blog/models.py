from django.db import models
from mdeditor.fields import MDTextField

# Create your models here.

class Article(models.Model):
    title = models.CharField(max_length=200)
    text = MDTextField()
    url = models.TextField()
    update_time = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "article"

    def __str__(self):
        return f"Article <{self.title}>"

class Tag(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)
    permalink = models.CharField(max_length=200)

    class Meta:
        db_table = "tag"

class Category(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)
    permalink = models.CharField(max_length=200)

    class Meta:
        db_table = "category"


