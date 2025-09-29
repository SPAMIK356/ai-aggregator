from __future__ import annotations

import json
from typing import Dict, Optional

from django.conf import settings
from openai import OpenAI

from .models import RewriterConfig


def get_active_config() -> Optional[RewriterConfig]:
	cfg = RewriterConfig.objects.order_by("-updated_at").first()
	return cfg if cfg and cfg.is_enabled else None


def rewrite_article(title: str, content: str) -> Optional[Dict[str, str]]:
	cfg = get_active_config()
	if not cfg:
		return None
	api_key = getattr(settings, "OPENAI_API_KEY", None)
	if not api_key:
		return None

	client = OpenAI(api_key=api_key)

	system_prompt = cfg.prompt or (
		"You rewrite and clean AI-related articles into concise Russian. Return json with keys 'title' and 'content'."
	)
	# Ensure the word 'json' (lowercase) is present to satisfy response_format requirements
	if "json" not in system_prompt.lower():
		system_prompt = system_prompt.strip() + " Return json object with keys 'title' and 'content'."
	user_payload = {
		"title": title,
		"content": content,
	}

	response = client.chat.completions.create(
		model=cfg.model,
		messages=[
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
		],
		response_format={"type": "json_object"},
	)
	text = response.choices[0].message.content or "{}"
	try:
		data = json.loads(text)
		return {"title": data.get("title") or title, "content": data.get("content") or content}
	except Exception:
		return {"title": title, "content": content}


