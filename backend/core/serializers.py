from rest_framework import serializers

from .models import AuthorColumn, NewsItem, SitePage, Hashtag, SocialLink


def _abs_url(request, url: str) -> str:
	if not url:
		return ""
	if url.startswith("http://") or url.startswith("https://"):
		return url
	try:
		if request is not None:
			return request.build_absolute_uri(url)
	except Exception:
		pass
	return url


class HashtagSerializer(serializers.ModelSerializer):
	class Meta:
		model = Hashtag
		fields = ["id", "slug", "name", "is_active", "updated_at"]


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
		request = self.context.get("request") if hasattr(self, "context") else None
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return _abs_url(request, url)
		return _abs_url(request, obj.image_url or "")

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
		request = self.context.get("request") if hasattr(self, "context") else None
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return _abs_url(request, url)
		return _abs_url(request, obj.image_url or "")

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
		request = self.context.get("request") if hasattr(self, "context") else None
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return _abs_url(request, url)
		return _abs_url(request, obj.image_url or "")

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
		request = self.context.get("request") if hasattr(self, "context") else None
		if getattr(obj, "image_file", None):
			url = obj.image_file.url if hasattr(obj.image_file, 'url') else ""
			return _abs_url(request, url)
		return _abs_url(request, obj.image_url or "")

	def get_hashtags(self, obj: AuthorColumn):
		items = getattr(obj, "hashtags", None).all() if hasattr(obj, "hashtags") else []
		return [{"slug": h.slug, "name": h.name} for h in items]


class SitePageSerializer(serializers.ModelSerializer):
	class Meta:
		model = SitePage
		fields = ["slug", "title", "body", "updated_at"]


class SocialLinkSerializer(serializers.ModelSerializer):
	icon_url = serializers.SerializerMethodField()

	class Meta:
		model = SocialLink
		fields = ["id", "name", "url", "icon_url", "order", "updated_at"]

	def get_icon_url(self, obj: SocialLink) -> str:
		request = self.context.get("request") if hasattr(self, "context") else None
		if getattr(obj, "icon", None):
			try:
				return _abs_url(request, obj.icon.url)
			except Exception:
				return ""
		return ""

