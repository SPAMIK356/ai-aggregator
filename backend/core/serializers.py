from rest_framework import serializers

from .models import AuthorColumn, NewsItem


class NewsItemSerializer(serializers.ModelSerializer):
	resolved_image = serializers.SerializerMethodField()

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
		]

	def get_resolved_image(self, obj: NewsItem) -> str:
		request = self.context.get("request") if hasattr(self, 'context') else None
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return request.build_absolute_uri(url) if request and url and url.startswith("/") else url
		return obj.image_url or ""


class NewsItemDetailSerializer(serializers.ModelSerializer):
	resolved_image = serializers.SerializerMethodField()

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
		]

	def get_resolved_image(self, obj: NewsItem) -> str:
		request = self.context.get("request") if hasattr(self, 'context') else None
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return request.build_absolute_uri(url) if request and url and url.startswith("/") else url
		return obj.image_url or ""


class AuthorColumnListSerializer(serializers.ModelSerializer):
	class Meta:
		model = AuthorColumn
		fields = ["id", "title", "author_name", "published_at"]


class AuthorColumnDetailSerializer(serializers.ModelSerializer):
	resolved_image = serializers.SerializerMethodField()

	class Meta:
		model = AuthorColumn
		fields = ["id", "title", "author_name", "published_at", "content_body", "image_url", "resolved_image"]

	def get_resolved_image(self, obj: AuthorColumn) -> str:
		request = self.context.get("request") if hasattr(self, 'context') else None
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return request.build_absolute_uri(url) if request and url and url.startswith("/") else url
		return obj.image_url or ""


