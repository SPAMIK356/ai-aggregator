from django.urls import path

from .views import (
	AuthorColumnDetailView,
	AuthorColumnListView,
	NewsItemDetailView,
	NewsItemListView,
	AuthorColumnCreateView,
	NewsItemCreateView,
	SitePageDetailView,
	UnifiedPostListView,
	SimilarPostsView,
	HashtagListView,
	ThemeListView,
	SocialLinkListView,
	NextNewsItemView,
	NextAuthorColumnView,
)


urlpatterns = [
	path("news/", NewsItemListView.as_view(), name="news-list"),
	path("news/<int:pk>/", NewsItemDetailView.as_view(), name="news-detail"),
    path("news/create/", NewsItemCreateView.as_view(), name="news-create"),
	path("columns/", AuthorColumnListView.as_view(), name="column-list"),
	path("columns/<int:pk>/", AuthorColumnDetailView.as_view(), name="column-detail"),
    path("columns/create/", AuthorColumnCreateView.as_view(), name="column-create"),
	path("posts/", UnifiedPostListView.as_view(), name="post-list"),
	path("posts/similar/", SimilarPostsView.as_view(), name="post-similar"),
	path("social-links/", SocialLinkListView.as_view(), name="social-link-list"),
	path("news/<int:pk>/next/", NextNewsItemView.as_view(), name="news-next"),
	path("columns/<int:pk>/next/", NextAuthorColumnView.as_view(), name="column-next"),
	path("hashtags/", HashtagListView.as_view(), name="hashtag-list"),
	path("meta/themes/", ThemeListView.as_view(), name="theme-list"),
	# Site pages by slug (footer/about/contact/privacy/terms)
	path("pages/<slug:slug>/", SitePageDetailView.as_view(), name="page-detail"),
]


