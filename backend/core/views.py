from rest_framework import generics, parsers, status
from rest_framework.response import Response
from django.db import transaction

from .models import AuthorColumn, NewsItem
from .serializers import (
	AuthorColumnDetailSerializer,
	AuthorColumnListSerializer,
	NewsItemDetailSerializer,
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


class NewsItemDetailView(generics.RetrieveAPIView):
	queryset = NewsItem.objects.all()
	serializer_class = NewsItemDetailSerializer


class AuthorColumnCreateView(generics.CreateAPIView):
	queryset = AuthorColumn.objects.all()
	serializer_class = AuthorColumnDetailSerializer
	parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]

	@transaction.atomic
	def post(self, request, *args, **kwargs):
		# Accept either multipart (image_file + fields) or JSON (image_url)
		title = request.data.get("title", "").strip()
		author_name = request.data.get("author_name", "").strip()
		content_body = request.data.get("content_body", "").strip()
		image_url = request.data.get("image_url", "").strip()
		image_file = request.data.get("image_file")
		if not title or not author_name:
			return Response({"error": "title and author_name are required"}, status=status.HTTP_400_BAD_REQUEST)
		obj = AuthorColumn.objects.create(
			title=title,
			author_name=author_name,
			content_body=content_body,
			image_url=image_url,
		)
		if image_file:
			obj.image_file = image_file
			obj.save(update_fields=["image_file", "updated_at"])
		ser = self.get_serializer(obj, context={"request": request})
		return Response(ser.data, status=status.HTTP_201_CREATED)


class NewsItemCreateView(generics.CreateAPIView):
	queryset = NewsItem.objects.all()
	serializer_class = NewsItemDetailSerializer
	parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]

	@transaction.atomic
	def post(self, request, *args, **kwargs):
		# Allow admin to post news with either external image_url or uploaded image_file
		title = request.data.get("title", "").strip()
		original_url = request.data.get("original_url", "").strip()
		description = request.data.get("description", "").strip()
		source_name = request.data.get("source_name", "").strip()
		image_url = request.data.get("image_url", "").strip()
		image_file = request.data.get("image_file")
		if not title:
			return Response({"error": "title is required"}, status=status.HTTP_400_BAD_REQUEST)
		# Ensure a unique original_url for internal posts
		internal_url = original_url or f"/internal/news/{timezone.now().timestamp()}"
		obj = NewsItem.objects.create(
			title=title,
			original_url=internal_url,
			description=description,
			source_name=source_name,
			image_url=image_url,
		)
		if image_file:
			obj.image_file = image_file
			obj.save(update_fields=["image_file", "updated_at"])
		ser = self.get_serializer(obj, context={"request": request})
		return Response(ser.data, status=status.HTTP_201_CREATED)


