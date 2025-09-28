from rest_framework import serializers

from .models import AuthorColumn, NewsItem


class NewsItemSerializer(serializers.ModelSerializer):
	class Meta:
		model = NewsItem
		fields = [
			"id",
			"title",
			"original_url",
			"description",
			"published_at",
			"source_name",
		]


class AuthorColumnListSerializer(serializers.ModelSerializer):
	class Meta:
		model = AuthorColumn
		fields = ["id", "title", "author_name", "published_at"]


class AuthorColumnDetailSerializer(serializers.ModelSerializer):
	class Meta:
		model = AuthorColumn
		fields = ["id", "title", "author_name", "published_at", "content_body"]


