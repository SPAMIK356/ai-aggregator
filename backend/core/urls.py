from django.urls import path

from .views import AuthorColumnDetailView, AuthorColumnListView, NewsItemListView


urlpatterns = [
	path("news/", NewsItemListView.as_view(), name="news-list"),
	path("columns/", AuthorColumnListView.as_view(), name="column-list"),
	path("columns/<int:pk>/", AuthorColumnDetailView.as_view(), name="column-detail"),
]


