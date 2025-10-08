from rest_framework import serializers

from .models import AuthorColumn, NewsItem, SitePage, Hashtag


class NewsItemSerializer(serializers.ModelSerializer):
	resolved_image = serializers.SerializerMethodField()
	hashtags = serializers.SerializerMethodField()

	class Meta:
		model = NewsItem
		fields = [
			"id",
			"title",
			"original_url",
			"description",
			"published_at",
			"source_name",
			"image_url",
			"resolved_image",
			"theme",
			"hashtags",
		]

	def get_resolved_image(self, obj: NewsItem) -> str:
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return url
		return obj.image_url or ""

	def get_hashtags(self, obj: NewsItem):
		items = getattr(obj, "hashtags", None).all() if hasattr(obj, "hashtags") else []
		return [{"slug": h.slug, "name": h.name} for h in items]


class NewsItemDetailSerializer(serializers.ModelSerializer):
	resolved_image = serializers.SerializerMethodField()
	hashtags = serializers.SerializerMethodField()

	class Meta:
		model = NewsItem
		fields = [
			"id",
			"title",
			"original_url",
			"description",
			"published_at",
			"source_name",
			"image_url",
			"resolved_image",
			"theme",
			"hashtags",
		]

	def get_resolved_image(self, obj: NewsItem) -> str:
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return url
		return obj.image_url or ""

	def get_hashtags(self, obj: NewsItem):
		items = getattr(obj, "hashtags", None).all() if hasattr(obj, "hashtags") else []
		return [{"slug": h.slug, "name": h.name} for h in items]


class AuthorColumnListSerializer(serializers.ModelSerializer):
	resolved_image = serializers.SerializerMethodField()
	hashtags = serializers.SerializerMethodField()
	class Meta:
		model = AuthorColumn
		fields = ["id", "title", "author_name", "published_at", "image_url", "resolved_image", "theme", "hashtags"]

	def get_resolved_image(self, obj: AuthorColumn) -> str:
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return url
		return obj.image_url or ""

	def get_hashtags(self, obj: AuthorColumn):
		items = getattr(obj, "hashtags", None).all() if hasattr(obj, "hashtags") else []
		return [{"slug": h.slug, "name": h.name} for h in items]


class AuthorColumnDetailSerializer(serializers.ModelSerializer):
	resolved_image = serializers.SerializerMethodField()
	hashtags = serializers.SerializerMethodField()

	class Meta:
		model = AuthorColumn
		fields = ["id", "title", "author_name", "published_at", "content_body", "image_url", "resolved_image", "theme", "hashtags"]

	def get_resolved_image(self, obj: AuthorColumn) -> str:
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return url
		return obj.image_url or ""

	def get_hashtags(self, obj: AuthorColumn):
		items = getattr(obj, "hashtags", None).all() if hasattr(obj, "hashtags") else []
		return [{"slug": h.slug, "name": h.name} for h in items]


class SitePageSerializer(serializers.ModelSerializer):
	class Meta:
		model = SitePage
		fields = ["slug", "title", "body", "updated_at"]


