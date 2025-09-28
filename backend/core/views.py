from rest_framework import generics

from .models import AuthorColumn, NewsItem
from .serializers import (
	AuthorColumnDetailSerializer,
	AuthorColumnListSerializer,
	NewsItemSerializer,
)


class NewsItemListView(generics.ListAPIView):
	queryset = NewsItem.objects.order_by("-published_at", "-id")
	serializer_class = NewsItemSerializer


class AuthorColumnListView(generics.ListAPIView):
	queryset = AuthorColumn.objects.order_by("-published_at", "-id")
	serializer_class = AuthorColumnListSerializer


class AuthorColumnDetailView(generics.RetrieveAPIView):
	queryset = AuthorColumn.objects.all()
	serializer_class = AuthorColumnDetailSerializer


