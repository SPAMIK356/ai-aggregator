from django.urls import path

from .views import (git 
    AuthorColumnDetailView,
    AuthorColumnListView,
    NewsItemDetailView,
    NewsItemListView,
    AuthorColumnCreateView,
    NewsItemCreateView,
)


urlpatterns = [
	path("news/", NewsItemListView.as_view(), name="news-list"),
	path("news/<int:pk>/", NewsItemDetailView.as_view(), name="news-detail"),
    path("news/create/", NewsItemCreateView.as_view(), name="news-create"),
	path("columns/", AuthorColumnListView.as_view(), name="column-list"),
	path("columns/<int:pk>/", AuthorColumnDetailView.as_view(), name="column-detail"),
    path("columns/create/", AuthorColumnCreateView.as_view(), name="column-create"),
]


