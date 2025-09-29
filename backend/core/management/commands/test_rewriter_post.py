from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import NewsItem
from core.rewriter import rewrite_article


class Command(BaseCommand):
	help = (
		"Test AI rewriter and posting pipeline. By default runs a dry run and prints the rewritten JSON.\n"
		"Use --save to create a NewsItem (will also enqueue an OutboxEvent via signals)."
	)

	def add_arguments(self, parser):
		parser.add_argument("--title", default="Test: AI Aggregator", help="Original title")
		parser.add_argument("--content", default="This is a <b>test</b> content sample.", help="Original HTML/content")
		parser.add_argument("--save", action="store_true", help="Create a NewsItem after rewriting")
		parser.add_argument("--no-rewrite", action="store_true", help="Skip AI and post as-is")

	def handle(self, *args, **opts):
		title = opts["title"]
		content = opts["content"]
		use_ai = not opts["no_rewrite"]
		rew = {"title": title, "content": content}
		if use_ai:
			maybe = rewrite_article(title, content)
			if maybe:
				rew = maybe
				self.stdout.write(self.style.SUCCESS("AI rewrite succeeded"))
			else:
				self.stdout.write("AI rewrite disabled or not configured; using original content")

		self.stdout.write(f"Rewritten JSON:\n{{\n  'title': {rew['title']!r},\n  'content': <{len(rew['content'])} chars>\n}}")

		if not opts["save"]:
			self.stdout.write(self.style.WARNING("Dry run only. Use --save to create a NewsItem."))
			return

		item = NewsItem.objects.create(
			title=rew["title"][:500],
			original_url="https://example.test/test-rewriter",
			description=rew["content"][:10000],
			published_at=timezone.now(),
			source_name="Test Rewriter",
		)
		self.stdout.write(self.style.SUCCESS(f"Created NewsItem id={item.id}"))


