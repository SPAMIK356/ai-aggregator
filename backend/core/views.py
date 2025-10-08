from rest_framework import generics, parsers, status
from rest_framework.response import Response
from django.db import transaction

from .models import AuthorColumn, NewsItem, SitePage, Hashtag
from django.db.models import Q
from .serializers import (
	AuthorColumnDetailSerializer,
	AuthorColumnListSerializer,
	NewsItemDetailSerializer,
	NewsItemSerializer,
    SitePageSerializer,
)


class NewsItemListView(generics.ListAPIView):
	queryset = NewsItem.objects.order_by("-published_at", "-id")
	serializer_class = NewsItemSerializer
	def get_queryset(self):
		qs = super().get_queryset()
		q = (self.request.query_params.get("q") or "").strip()
		theme = (self.request.query_params.get("theme") or "").strip().upper()
		if q:
			qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
		if theme in (NewsItem.Theme.AI, NewsItem.Theme.CRYPTO):
			qs = qs.filter(theme=theme)
		return qs


class AuthorColumnListView(generics.ListAPIView):
	queryset = AuthorColumn.objects.order_by("-published_at", "-id")
	serializer_class = AuthorColumnListSerializer
	def get_queryset(self):
		qs = super().get_queryset()
		q = (self.request.query_params.get("q") or "").strip()
		theme = (self.request.query_params.get("theme") or "").strip().upper()
		if q:
			qs = qs.filter(Q(title__icontains=q) | Q(content_body__icontains=q))
		if theme in (NewsItem.Theme.AI, NewsItem.Theme.CRYPTO):
			qs = qs.filter(theme=theme)
		return qs


class UnifiedPostListView(generics.ListAPIView):
	"""Return union of NewsItem and AuthorColumn with normalized fields.

	Supports ?q= and ?theme=AI|CRYPTO
	"""
	serializer_class = None  # not used

	def list(self, request, *args, **kwargs):
		q = (request.query_params.get("q") or "").strip()
		theme = (request.query_params.get("theme") or "").strip().upper()
		news_qs = NewsItem.objects.order_by("-published_at", "-id")
		col_qs = AuthorColumn.objects.order_by("-published_at", "-id")
		if q:
			news_qs = news_qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
			col_qs = col_qs.filter(Q(title__icontains=q) | Q(content_body__icontains=q))
		if theme in (NewsItem.Theme.AI, NewsItem.Theme.CRYPTO):
			news_qs = news_qs.filter(theme=theme)
			col_qs = col_qs.filter(theme=theme)
		def map_news(n: NewsItem):
			return {
				"id": n.id,
				"type": "news",
				"title": n.title,
				"snippet": (n.description or "")[:300],
				"resolved_image": getattr(n.image_file, 'url', None) if getattr(n, 'image_file', None) else (n.image_url or ""),
				"theme": n.theme,
				"hashtags": [{"slug": h.slug, "name": h.name} for h in getattr(n, 'hashtags').all()] if hasattr(n, 'hashtags') else [],
				"published_at": n.published_at,
			}
		def map_col(c: AuthorColumn):
			return {
				"id": c.id,
				"type": "column",
				"title": c.title,
				"snippet": (c.content_body or "")[:300],
				"resolved_image": getattr(c, 'image_file', None).url if getattr(c, 'image_file', None) else (c.image_url or ""),
				"theme": c.theme,
				"hashtags": [{"slug": h.slug, "name": h.name} for h in getattr(c, 'hashtags').all()] if hasattr(c, 'hashtags') else [],
				"published_at": c.published_at,
			}
		items = [*map(map_news, news_qs[:50]), *map(map_col, col_qs[:50])]
		# Sort merged items by published_at desc
		items.sort(key=lambda x: (x["published_at"], x["id"]), reverse=True)
		return Response({"results": items[:50]})


class SimilarPostsView(generics.GenericAPIView):
	def get(self, request, *args, **kwargs):
		item_type = (request.query_params.get("type") or "news").strip().lower()
		item_id = int(request.query_params.get("id") or 0)
		limit = int(request.query_params.get("limit") or 2)
		limit = max(1, min(10, limit))
		if item_type == "column":
			base = AuthorColumn.objects.filter(pk=item_id).first()
			if not base:
				return Response({"results": []})
			base_tags = list(base.hashtags.values_list("id", flat=True)) if hasattr(base, "hashtags") else []
			qs = AuthorColumn.objects.exclude(pk=base.pk).filter(theme=base.theme)
			if base_tags:
				qs = qs.filter(hashtags__in=base_tags).distinct()
			qs = qs.order_by("-published_at", "-id")[:limit]
			results = [{
				"id": c.id,
				"type": "column",
				"title": c.title,
				"resolved_image": getattr(c, 'image_file', None).url if getattr(c, 'image_file', None) else (c.image_url or ""),
				"theme": c.theme,
				"hashtags": [{"slug": h.slug, "name": h.name} for h in getattr(c, 'hashtags').all()] if hasattr(c, 'hashtags') else [],
				"published_at": c.published_at,
			} for c in qs]
			return Response({"results": results})
		else:
			base = NewsItem.objects.filter(pk=item_id).first()
			if not base:
				return Response({"results": []})
			base_tags = list(base.hashtags.values_list("id", flat=True)) if hasattr(base, "hashtags") else []
			qs = NewsItem.objects.exclude(pk=base.pk).filter(theme=base.theme)
			if base_tags:
				qs = qs.filter(hashtags__in=base_tags).distinct()
			qs = qs.order_by("-published_at", "-id")[:limit]
			results = [{
				"id": n.id,
				"type": "news",
				"title": n.title,
				"resolved_image": getattr(n, 'image_file', None).url if getattr(n, 'image_file', None) else (n.image_url or ""),
				"theme": n.theme,
				"hashtags": [{"slug": h.slug, "name": h.name} for h in getattr(n, 'hashtags').all()] if hasattr(n, 'hashtags') else [],
				"published_at": n.published_at,
			} for n in qs]
			return Response({"results": results})


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
		# required theme
		theme = (request.data.get("theme") or "").strip().upper() or NewsItem.Theme.AI
		if theme not in (NewsItem.Theme.AI, NewsItem.Theme.CRYPTO):
			return Response({"error": "invalid theme"}, status=status.HTTP_400_BAD_REQUEST)
		image_file = request.data.get("image_file")
		if not title or not author_name:
			return Response({"error": "title and author_name are required"}, status=status.HTTP_400_BAD_REQUEST)
		obj = AuthorColumn.objects.create(
			title=title,
			author_name=author_name,
			content_body=content_body,
			image_url=image_url,
			theme=theme,
		)
		# optional hashtags (list of slugs)
		try:
			hashtags = request.data.getlist("hashtags") if hasattr(request.data, "getlist") else request.data.get("hashtags")
			if isinstance(hashtags, str):
				import json as _json
				try:
					hashtags = _json.loads(hashtags)
				except Exception:
					hashtags = [h.strip() for h in hashtags.split(",") if h.strip()]
			if isinstance(hashtags, list) and hashtags:
				from .models import Hashtag
				objs = list(Hashtag.objects.filter(slug__in=[str(s).lower() for s in hashtags], is_active=True))
				if objs:
					obj.hashtags.add(*objs)
		except Exception:
			pass
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
		# required theme
		theme = (request.data.get("theme") or "").strip().upper() or NewsItem.Theme.AI
		if theme not in (NewsItem.Theme.AI, NewsItem.Theme.CRYPTO):
			return Response({"error": "invalid theme"}, status=status.HTTP_400_BAD_REQUEST)
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
			theme=theme,
		)
		# optional hashtags (list of slugs)
		try:
			hashtags = request.data.getlist("hashtags") if hasattr(request.data, "getlist") else request.data.get("hashtags")
			if isinstance(hashtags, str):
				import json as _json
				try:
					hashtags = _json.loads(hashtags)
				except Exception:
					hashtags = [h.strip() for h in hashtags.split(",") if h.strip()]
			if isinstance(hashtags, list) and hashtags:
				from .models import Hashtag
				objs = list(Hashtag.objects.filter(slug__in=[str(s).lower() for s in hashtags], is_active=True))
				if objs:
					obj.hashtags.add(*objs)
		except Exception:
			pass
		if image_file:
			obj.image_file = image_file
			obj.save(update_fields=["image_file", "updated_at"])
		ser = self.get_serializer(obj, context={"request": request})
		return Response(ser.data, status=status.HTTP_201_CREATED)


class SitePageDetailView(generics.RetrieveAPIView):
	lookup_field = "slug"
	queryset = SitePage.objects.all()
	serializer_class = SitePageSerializer


