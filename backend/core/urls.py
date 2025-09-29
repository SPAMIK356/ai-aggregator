from django.urls import path

from .views import AuthorColumnDetailView, AuthorColumnListView, NewsItemDetailView, NewsItemListView


urlpatterns = [
	path("news/", NewsItemListView.as_view(), name="news-list"),
	path("news/<int:pk>/", NewsItemDetailView.as_view(), name="news-detail"),
	path("columns/", AuthorColumnListView.as_view(), name="column-list"),
	path("columns/<int:pk>/", AuthorColumnDetailView.as_view(), name="column-detail"),
]


