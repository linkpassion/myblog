"""myblog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from blog.views import IndexView, ArticleDetailView, ArchiveView, TagView, CategoryView, AboutView, ContentView, \
    ArticleApiView
from django.views.decorators.cache import cache_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',  cache_page(60 * 5)(IndexView.as_view()), name='index'),
    path('api/article', ArticleApiView.as_view()),
    path('<str:year>/<str:article_title>', cache_page(60 * 5)(ArticleDetailView.as_view())),
    path('tags/', cache_page(60 * 5)(TagView.as_view())),
    path('archives/', cache_page(60 * 5)(ArchiveView.as_view())),
    path('categories/', cache_page(60 * 5)(CategoryView.as_view())),
    path('about/', cache_page(60 * 5)(AboutView.as_view())),
    path('mdeditor/', include("mdeditor.urls")),
    path('content.json', ContentView.as_view()),
] + static(settings.STATIC_URL) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

