import time

from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView, View
from rest_framework.views import APIView
from .models import Article, Tag, Category
from django.http.response import JsonResponse
from django.core import serializers
from django.core.cache import cache
import math
from pprint import pprint
import markdown
from django.db.models import Count
from .serializers import ArticleSerializer
import json


# Create your views here.


def base_data():
    """
    基础数据
    """
    redis_key = "article_cache"
    redis_value = cache.get(redis_key)
    if redis_value:
        print("hit cache")
        serializers_articles = json.loads(redis_value)

    else:
        # article_list
        article_list = Article.objects.order_by("-create_time")
        for article in article_list:
            article.pub_date = article.create_time.strftime("%m-%d").replace("-", "月") + "日"
            article.upd_time = article.create_time.strftime("%Y-%m-%d")
            article.text_length = len(article.text)
            article.read_time = math.ceil(len(article.text) / 180) if article.text else 0
            article.cate_list = article.category_set.values
            article.tag_list = article.tag_set.values

        # archive_list
        select_data = {"months": """DATE_FORMAT(create_time,'%%Y-%%m')"""}
        archive_list = Article.objects.extra(select=select_data).values("months").annotate(Count("id")).order_by("-months")

        # tag_list
        tag_list = Tag.objects.values("slug", "permalink").annotate(Count("id")).order_by()

        # category_list
        category_list = Category.objects.values("slug", "permalink").annotate(Count("id")).order_by()

        context = {
            "archive_list": archive_list,
            "article_list": article_list,
            "tag_list": tag_list,
            "category_list": category_list,
        }


    return context


class IndexView(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):

        context = base_data()

        return self.render_to_response(context)

class ArticleDetailView(TemplateView):
    template_name = "detail.html"

    def get(self, request, *args, **kwargs):

        # article
        article = Article.objects.get(url=request.path)
        content = ""
        for line in article.text.split("\n"):
            content += line.strip(" ") if "'''" in line else line + "\n"

        pprint(content)
        article.content = markdown.markdown(content,
                                            extensions=[
                                                'markdown.extensions.extra',
                                                'markdown.extensions.codehilite',
                                                'markdown.extensions.toc',
                                            ])
        context = {
            "article": article,
        }

        try:
            next_article = Article.objects.raw(
                f"select * from {Article._meta.db_table} where id<{article.id} order by id desc limit 1")
            context.update({
                "next_article": next_article[0]
            })
        except:
            print("could not find next article")

        try:
            pre_article = Article.objects.raw(
                f"select * from {Article._meta.db_table} where id>{article.id} order by id limit 1")
            context.update({
                "pre_article": pre_article[0]
            })
        except:
            print("could not find pre article")

        context.update(base_data())

        return self.render_to_response(context)


class ArchiveView(TemplateView):
    template_name = "archives.html"

    def get(self, request, *args, **kwargs):
        article_list = Article.objects.order_by("-create_time")
        tmp_dict = {}
        for article in article_list:
            year = article.create_time.strftime("%Y")
            article.pub_date = article.create_time.strftime("%Y-%m-%d")
            tmp_dict.setdefault(year, {"year": year, "article_list": []})
            tmp_dict[year]['article_list'].append(article)

        context = {
            "archives": list(tmp_dict.values()),
            "article_count": len(article_list)
        }
        context.update(base_data())

        return self.render_to_response(context)


class TagView(TemplateView):
    template_name = "tag.html"

    def get(self, request, *args, **kwargs):

        tag_list = Tag.objects.all()
        tmp_dict = {}
        for tag in tag_list:
            name = tag.slug
            tmp_dict.setdefault(name, {"name": name, "article_list": []})
            article = tag.article
            article.pub_date = article.create_time.strftime("%Y-%m-%d")
            article.tag_list = article.tag_set.values
            tmp_dict[name]['article_list'].append(article)

        for name in tmp_dict:
            tmp_dict[name]['count'] = len(tmp_dict[name]["article_list"])

        context = {
            "tags": list(tmp_dict.values()),
        }

        context.update(base_data())

        return self.render_to_response(context)


class CategoryView(TemplateView):
    template_name = "category.html"

    def get(self, request, *args, **kwargs):

        category_list = Category.objects.all()
        tmp_dict = {}
        for category in category_list:
            name = category.slug
            tmp_dict.setdefault(name, {"name": name, "article_list": []})
            article = category.article
            article.pub_date = article.create_time.strftime("%Y-%m-%d")
            tmp_dict[name]['article_list'].append(article)
        for name in tmp_dict:
            tmp_dict[name]['count'] = len(tmp_dict[name]["article_list"])

        context = {
            "categories": list(tmp_dict.values()),
        }

        context.update(base_data())

        return self.render_to_response(context)


class AboutView(TemplateView):
    template_name = "about.html"

    def get(self, request, *args, **kwargs):
        context = base_data()

        return self.render_to_response(context)


class ContentView(View):
    def get(self, request):
        article_list = Article.objects.order_by("-create_time")
        tmp_dict = {}
        for article in article_list:
            tmp_dict.setdefault("posts", [])
            tmp_dict["posts"].append({
                "title": article.title,
                "slug": article.title,
                "comments": True,
                "date": article.create_time.strftime("%Y-%m-%d %H-%M-%S"),
                "excerpt": "",
                "link": "",
                "path": article.url.lstrip('/'),
                "parmalink": "http://127.0.0.1:8000" + article.url,
                "text": article.text,
                "update": article.update_time.strftime("%Y-%m-%d %H-%M-%S"),
            })
        tmp_dict.setdefault("pages", [])


        content_str = json.dumps(tmp_dict)


        return JsonResponse(json.loads(content_str), safe=False)



class ArticleApiView(APIView):
    def get(self, request, *args, **kwargs):
        """
        article?limit_num=2
        :param args:
        :param kwargs:
        :return:
        """
        limit_num = request.GET.get("limit_num")
        if limit_num:
            article_array = Article.objects.all()[:int(limit_num)]
        else:
            article_array = Article.objects.all()
        se_article_array = ArticleSerializer(article_array, many=True)
        return JsonResponse({
            "status": 200,
            "data": se_article_array.data
        }, safe=False)

    def post(self, request, *args, **kwargs):
        """
        添加文章的时候, 需要带上category和tag的信息
        只要article, category, tag有一方报错的时候, 当前文章都算添加失败.
        所以我们应该适用事务进行包装
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            message = {"status": 200}
            with transaction.atomic():
                title = request.POST['title']
                text = request.POST['text']
                categories = json.loads(request.POST['categories'])
                tags = json.loads(request.POST['tags'])

                article_data = {
                    "title": title,
                    "text": text,
                    "url": f"/{time.strftime('%Y')}/{title}.html"
                }
                se_article = ArticleSerializer(data=article_data)
                se_article.is_valid()
                article = se_article.create(se_article.data)
                article.save()

                for category in categories:
                    cate = Category(
                        name=category['name'],
                        slug=category['slug'],
                        uri=f"/categories/"
                    )
                    cate.article = article
                    cate.save()

                for tag in tags:
                    tag = Tag(
                        name=tag['name'],
                        slug=tag['slug'],
                        uri=f"/tags/"
                    )
                    tag.article = article
                    tag.save()
        except:
            message = {"status": 500, "reason": "添加文章失败"}
        finally:
            response = JsonResponse(message, safe=False)
            response['Access-Control-Allow-Origin'] = "*"  # *表示任意域名
            response['Access-Control-Allow-Headers'] = "*"
            response['Access-Control-Allow-Methods'] = "OPTIONS, POST, GET"

            return response

    def put(self, request, *args, **kwargs):
        """
        重点是如何获取携带的参数
        request.POST(key)
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        pass

    def delete(self, request, *args, **kwargs):
        pass
