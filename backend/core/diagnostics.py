"""Diagnostic utilities for testing the full news aggregator pipeline.

Provides detailed logging and step-by-step verification of ALL pipeline stages
in the exact order they are applied:
1. Configuration Check
2. Daily Post Limits
3. Keyword Filter
4. Min Chars Check
5. AI Rewriter
6. Ad Classifier
7. EN→RU Translator
8. Image Prompt Generation (OpenAI)
9. Image Generation (fal-ai)
10. Telegram Rewriter
11. Telegram Delivery
12. Outbox Status
"""
from __future__ import annotations

import re
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone


@dataclass
class DiagnosticStep:
    """Single step in the diagnostic pipeline."""
    name: str
    status: str = "pending"  # pending, running, success, error, skipped
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    duration_ms: Optional[float] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    raw_response: Optional[str] = None
    tokens_used: Optional[Dict[str, int]] = None
    
    def start(self):
        self.status = "running"
        self.started_at = time.time()
    
    def finish(self, success: bool = True, error: str = None):
        self.ended_at = time.time()
        self.duration_ms = (self.ended_at - (self.started_at or self.ended_at)) * 1000
        self.status = "success" if success else "error"
        if error:
            self.error = error
    
    def skip(self, reason: str = ""):
        self.status = "skipped"
        self.error = reason
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 2) if self.duration_ms else None,
            "input": self.input_data,
            "output": self.output_data,
            "error": self.error,
            "raw_response": self.raw_response,
            "tokens": self.tokens_used,
        }


@dataclass
class DiagnosticResult:
    """Full diagnostic run result."""
    steps: List[DiagnosticStep] = field(default_factory=list)
    overall_status: str = "pending"
    total_duration_ms: float = 0
    started_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "started_at": self.started_at,
            "steps": [s.to_dict() for s in self.steps],
        }


def run_full_diagnostic(
    test_title: str = "Test Article: AI Breakthrough in 2024",
    test_content: str = "Scientists have developed a revolutionary new algorithm that improves neural network efficiency by 50%. This breakthrough could transform machine learning applications across industries.",
    send_to_telegram: bool = False,
) -> DiagnosticResult:
    """Run a full diagnostic of all pipeline components in exact processing order.
    
    Args:
        test_title: Sample article title for testing
        test_content: Sample article content for testing
        send_to_telegram: If True, actually sends a test message to Telegram
        
    Returns:
        DiagnosticResult with detailed step-by-step information
    """
    import json
    result = DiagnosticResult()
    result.started_at = timezone.now().isoformat()
    overall_start = time.time()
    
    # Track content through the pipeline
    current_title = test_title
    current_content = test_content
    
    # ============================================================
    # STEP 1: Configuration Check
    # ============================================================
    step_config = DiagnosticStep(name="1. Configuration Check")
    result.steps.append(step_config)
    step_config.start()
    try:
        from .models import ParserConfig, RewriterConfig, TranslatorConfig, AdClassifierConfig, TelegramRewriterConfig, ImageGeneratorConfig, KeywordFilter, LinkFilter
        
        parser_cfg = ParserConfig.objects.order_by("-updated_at").first()
        rewriter_cfg = RewriterConfig.objects.order_by("-updated_at").first()
        translator_cfg = TranslatorConfig.objects.order_by("-updated_at").first()
        ad_cfg = AdClassifierConfig.objects.order_by("-updated_at").first()
        tg_rewriter_cfg = TelegramRewriterConfig.objects.order_by("-updated_at").first()
        img_cfg = ImageGeneratorConfig.objects.order_by("-updated_at").first()
        
        config_info = {
            "env": {
                "OPENAI_API_KEY": "✓ Set" if getattr(settings, "OPENAI_API_KEY", None) else "✗ Missing",
                "OPENAI_BASE_URL": getattr(settings, "OPENAI_BASE_URL", None) or "(default)",
                "TELEGRAM_BOT_TOKEN": "✓ Set" if getattr(settings, "TELEGRAM_BOT_TOKEN", None) else "✗ Missing",
                "TELEGRAM_CHANNEL": getattr(settings, "TELEGRAM_CHANNEL", None) or "✗ Missing",
            },
            "parser": {
                "max_posts_per_day": parser_cfg.max_posts_per_day if parser_cfg else "N/A",
                "max_posts_per_source_per_day": parser_cfg.max_posts_per_source_per_day if parser_cfg else "N/A",
                "min_chars": parser_cfg.min_chars if parser_cfg else "N/A",
            } if parser_cfg else "No ParserConfig",
            "features": {
                "rewriter": f"✓ Enabled ({rewriter_cfg.model})" if rewriter_cfg and rewriter_cfg.is_enabled else "✗ Disabled",
                "translator": f"✓ Enabled ({translator_cfg.model})" if translator_cfg and translator_cfg.is_enabled else "✗ Disabled",
                "ad_classifier": f"✓ Enabled ({ad_cfg.model})" if ad_cfg and ad_cfg.is_enabled else "✗ Disabled",
                "tg_rewriter": f"✓ Enabled ({tg_rewriter_cfg.model})" if tg_rewriter_cfg and tg_rewriter_cfg.is_enabled else "✗ Disabled",
                "image_generator": f"✓ Enabled ({img_cfg.fal_model})" if img_cfg and img_cfg.is_enabled else "✗ Disabled",
            },
            "filters": {
                "keyword_filters": KeywordFilter.objects.filter(is_active=True).count(),
                "link_filters": LinkFilter.objects.filter(is_active=True).count(),
            },
        }
        step_config.output_data = config_info
        step_config.finish(success=True)
    except Exception as e:
        step_config.finish(success=False, error=str(e))
        step_config.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 2: Daily Post Limits Check
    # ============================================================
    step_limits = DiagnosticStep(name="2. Daily Post Limits")
    result.steps.append(step_limits)
    step_limits.start()
    try:
        from .models import ParserConfig, NewsItem
        from django.db.models import Count
        
        cfg = ParserConfig.objects.order_by("-updated_at").first()
        today = timezone.now().date()
        
        # Count today's posts
        total_today = NewsItem.objects.filter(created_at__date=today).count()
        by_source = list(NewsItem.objects
            .filter(created_at__date=today)
            .values('source_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10])
        
        max_total = cfg.max_posts_per_day if cfg else 0
        max_per_source = cfg.max_posts_per_source_per_day if cfg else 0
        
        step_limits.output_data = {
            "limits_configured": {
                "max_posts_per_day": max_total or "unlimited",
                "max_posts_per_source_per_day": max_per_source or "unlimited",
            },
            "current_usage": {
                "total_posts_today": total_today,
                "remaining_total": (max_total - total_today) if max_total else "unlimited",
                "by_source": {s['source_name']: s['count'] for s in by_source},
            },
            "would_pass": (not max_total or total_today < max_total),
        }
        step_limits.finish(success=True)
    except Exception as e:
        step_limits.finish(success=False, error=str(e))
        step_limits.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 3: Keyword Filter Check
    # ============================================================
    step_keyword = DiagnosticStep(name="3. Keyword Filter")
    result.steps.append(step_keyword)
    step_keyword.start()
    step_keyword.input_data = {"title": current_title[:100], "content": current_content[:200]}
    try:
        from .models import KeywordFilter
        
        active_filters = list(KeywordFilter.objects.filter(is_active=True).values_list('phrase', flat=True))
        phrases_lc = [p.lower().strip() for p in active_filters if p.strip()]
        
        full_text = f"{current_title}\n{current_content}".lower()
        matched_keywords = [kw for kw in phrases_lc if kw in full_text]
        
        step_keyword.output_data = {
            "active_keywords": phrases_lc[:20],
            "total_keywords": len(phrases_lc),
            "matched": matched_keywords,
            "would_pass": len(matched_keywords) == 0,
        }
        step_keyword.finish(success=True)
    except Exception as e:
        step_keyword.finish(success=False, error=str(e))
        step_keyword.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 4: Link Filter Check
    # ============================================================
    step_link = DiagnosticStep(name="4. Link Filter")
    result.steps.append(step_link)
    step_link.start()
    step_link.input_data = {"content_preview": current_content[:200]}
    try:
        from .models import LinkFilter
        
        active_prefixes = list(LinkFilter.objects.filter(is_active=True).values_list('prefix', flat=True))
        
        # Simulate link stripping
        test_text = current_content
        stripped_links = []
        for prefix in active_prefixes:
            if prefix.strip():
                pattern = rf'https?://[^\s]*{re.escape(prefix.strip())}[^\s]*'
                matches = re.findall(pattern, test_text, re.IGNORECASE)
                stripped_links.extend(matches)
                test_text = re.sub(pattern, '', test_text, flags=re.IGNORECASE)
        
        step_link.output_data = {
            "active_prefixes": active_prefixes[:20],
            "links_that_would_be_stripped": stripped_links,
            "chars_before": len(current_content),
            "chars_after": len(test_text.strip()),
        }
        step_link.finish(success=True)
    except Exception as e:
        step_link.finish(success=False, error=str(e))
        step_link.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 5: Min Chars Check (Pre-Rewrite)
    # ============================================================
    step_min_chars = DiagnosticStep(name="5. Min Chars Check")
    result.steps.append(step_min_chars)
    step_min_chars.start()
    try:
        from .models import ParserConfig
        
        cfg = ParserConfig.objects.order_by("-updated_at").first()
        min_chars = cfg.min_chars if cfg else 0
        
        # Strip HTML for accurate count
        def strip_html(text):
            return re.sub(r'<[^>]+>', '', text or '')
        
        content_length = len(strip_html(current_content))
        
        step_min_chars.input_data = {
            "content_length": content_length,
            "min_chars_required": min_chars or "none",
        }
        step_min_chars.output_data = {
            "would_pass": (not min_chars or content_length >= min_chars),
            "chars_short": max(0, (min_chars or 0) - content_length),
        }
        step_min_chars.finish(success=True)
    except Exception as e:
        step_min_chars.finish(success=False, error=str(e))
        step_min_chars.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 6: AI Rewriter
    # ============================================================
    step_rewrite = DiagnosticStep(name="6. AI Rewriter")
    result.steps.append(step_rewrite)
    step_rewrite.start()
    step_rewrite.input_data = {"title": current_title[:100], "content": current_content[:200] + "..."}
    try:
        from .models import RewriterConfig
        cfg = RewriterConfig.objects.order_by("-updated_at").first()
        if not cfg or not cfg.is_enabled:
            step_rewrite.output_data = {"note": "Would use original content"}
            step_rewrite.skip("Rewriter is disabled in admin")
        else:
            from openai import OpenAI
            api_key = getattr(settings, "OPENAI_API_KEY", None)
            base_url = getattr(settings, "OPENAI_BASE_URL", None)
            if not api_key:
                step_rewrite.skip("OpenAI API key not configured")
            else:
                client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)
                system_prompt = cfg.prompt or "Rewrite this article professionally. Return JSON with 'title' and 'content' keys."
                response = client.chat.completions.create(
                    model=cfg.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Title: {current_title}\n\nContent: {current_content}"},
                    ],
                )
                raw = response.choices[0].message.content or ""
                step_rewrite.raw_response = raw[:2000]
                step_rewrite.tokens_used = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
                try:
                    data = json.loads(raw)
                    current_title = data.get("title", current_title)
                    current_content = data.get("content", current_content)
                    step_rewrite.output_data = {
                        "title": current_title[:200],
                        "content": current_content[:500] + "..." if len(current_content) > 500 else current_content,
                    }
                except json.JSONDecodeError:
                    step_rewrite.output_data = {"raw_text": raw[:500], "parse_error": "Could not parse JSON"}
                step_rewrite.finish(success=True)
    except Exception as e:
        step_rewrite.finish(success=False, error=f"{type(e).__name__}: {str(e)}")
        step_rewrite.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 7: Ad Classifier
    # ============================================================
    step_ad = DiagnosticStep(name="7. Ad Classifier")
    result.steps.append(step_ad)
    step_ad.start()
    step_ad.input_data = {"title": current_title[:100], "content": current_content[:200] + "..."}
    try:
        from .models import AdClassifierConfig
        cfg = AdClassifierConfig.objects.order_by("-updated_at").first()
        if not cfg or not cfg.is_enabled:
            step_ad.output_data = {"note": "All content passes (classifier disabled)"}
            step_ad.skip("Ad classifier is disabled in admin")
        else:
            from openai import OpenAI
            api_key = getattr(settings, "OPENAI_API_KEY", None)
            base_url = getattr(settings, "OPENAI_BASE_URL", None)
            if not api_key:
                step_ad.skip("OpenAI API key not configured")
            else:
                client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)
                system_prompt = cfg.prompt or "Classify if this is an advertisement. Return JSON with 'is_ad': true/false."
                response = client.chat.completions.create(
                    model=cfg.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Title: {current_title}\n\nContent: {current_content[:2000]}"},
                    ],
                )
                raw = response.choices[0].message.content or ""
                step_ad.raw_response = raw[:1000]
                step_ad.tokens_used = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
                try:
                    data = json.loads(raw)
                    is_ad = data.get("is_ad", False)
                    step_ad.output_data = {
                        "is_ad": is_ad,
                        "would_pass": not is_ad,
                        "confidence": data.get("confidence", "N/A"),
                        "reason": data.get("reason", "N/A"),
                    }
                except json.JSONDecodeError:
                    is_ad = "true" in raw.lower() or "yes" in raw.lower()
                    step_ad.output_data = {"raw_text": raw[:300], "inferred_is_ad": is_ad}
                step_ad.finish(success=True)
    except Exception as e:
        step_ad.finish(success=False, error=f"{type(e).__name__}: {str(e)}")
        step_ad.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 8: EN→RU Translator
    # ============================================================
    step_translate = DiagnosticStep(name="8. EN→RU Translator")
    result.steps.append(step_translate)
    step_translate.start()
    step_translate.input_data = {"title": current_title[:100], "content": current_content[:200] + "..."}
    translated_title_ru = ""
    translated_content_ru = ""
    try:
        from .models import TranslatorConfig
        cfg = TranslatorConfig.objects.order_by("-updated_at").first()
        if not cfg or not cfg.is_enabled:
            step_translate.skip("Translator is disabled in admin")
        else:
            from openai import OpenAI
            api_key = getattr(settings, "OPENAI_API_KEY", None)
            base_url = getattr(settings, "OPENAI_BASE_URL", None)
            if not api_key:
                step_translate.skip("OpenAI API key not configured")
            else:
                client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)
                system_prompt = cfg.prompt or "Translate to Russian. Return JSON with keys title_ru and content_ru."
                response = client.chat.completions.create(
                    model=cfg.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Title: {current_title}\n\nContent: {current_content}"},
                    ],
                )
                raw = response.choices[0].message.content or ""
                step_translate.raw_response = raw[:2000]
                step_translate.tokens_used = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
                try:
                    data = json.loads(raw)
                    translated_title_ru = data.get("title_ru", "")
                    translated_content_ru = data.get("content_ru", "")
                    step_translate.output_data = {
                        "title_ru": translated_title_ru[:200],
                        "content_ru": (translated_content_ru[:500] + "...") if len(translated_content_ru) > 500 else translated_content_ru,
                    }
                except json.JSONDecodeError:
                    step_translate.output_data = {"raw_text": raw[:500], "parse_error": "Could not parse JSON"}
                step_translate.finish(success=True)
    except Exception as e:
        step_translate.finish(success=False, error=f"{type(e).__name__}: {str(e)}")
        step_translate.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 9: Image Prompt Generation (OpenAI)
    # ============================================================
    step_img_prompt = DiagnosticStep(name="9. Image Prompt Generation")
    result.steps.append(step_img_prompt)
    step_img_prompt.start()
    generated_prompt = None
    try:
        from .models import ImageGeneratorConfig
        cfg = ImageGeneratorConfig.objects.order_by("-updated_at").first()
        if not cfg:
            step_img_prompt.skip("No ImageGeneratorConfig found")
        elif not cfg.is_enabled:
            step_img_prompt.skip("Image generation is disabled")
        else:
            from openai import OpenAI
            api_key = getattr(settings, "OPENAI_API_KEY", None)
            base_url = getattr(settings, "OPENAI_BASE_URL", None)
            if not api_key:
                step_img_prompt.skip("OpenAI API key not configured")
            elif not cfg.fal_api_key:
                step_img_prompt.skip("fal-ai API key not configured")
            else:
                step_img_prompt.input_data = {
                    "openai_model": cfg.openai_model,
                    "title": current_title[:100],
                }
                client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)
                system_prompt = cfg.prompt_generator_instructions or "Generate an image prompt for this article."
                response = client.chat.completions.create(
                    model=cfg.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Article Title: {current_title}\n\nArticle Content: {current_content[:1000]}"},
                    ],
                )
                generated_prompt = (response.choices[0].message.content or "").strip()
                step_img_prompt.raw_response = generated_prompt
                step_img_prompt.tokens_used = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
                step_img_prompt.output_data = {"generated_prompt": generated_prompt}
                step_img_prompt.finish(success=bool(generated_prompt))
    except Exception as e:
        step_img_prompt.finish(success=False, error=f"{type(e).__name__}: {str(e)}")
        step_img_prompt.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 10: Image Generation (fal-ai)
    # ============================================================
    step_img_gen = DiagnosticStep(name="10. Image Generation (fal-ai)")
    result.steps.append(step_img_gen)
    step_img_gen.start()
    generated_image_url = None
    try:
        from .models import ImageGeneratorConfig
        cfg = ImageGeneratorConfig.objects.order_by("-updated_at").first()
        if not cfg or not cfg.is_enabled:
            step_img_gen.skip("Image generation is disabled")
        elif not cfg.fal_api_key:
            step_img_gen.skip("fal-ai API key not configured")
        elif not generated_prompt:
            step_img_gen.skip("No prompt generated in previous step")
        else:
            import requests
            step_img_gen.input_data = {
                "fal_model": cfg.fal_model,
                "prompt": generated_prompt[:200],
                "aspect_ratio": cfg.aspect_ratio,
                "num_inference_steps": cfg.num_inference_steps,
            }
            
            aspect_dims = {
                "square": {"width": 1024, "height": 1024},
                "landscape_16_9": {"width": 1344, "height": 768},
                "landscape_4_3": {"width": 1152, "height": 896},
                "portrait_16_9": {"width": 768, "height": 1344},
                "portrait_4_3": {"width": 896, "height": 1152},
            }
            dimensions = aspect_dims.get(cfg.aspect_ratio, aspect_dims["landscape_16_9"])
            
            api_url = f"https://fal.run/{cfg.fal_model}"
            headers = {
                "Authorization": f"Key {cfg.fal_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "prompt": generated_prompt,
                "image_size": dimensions,
                "num_inference_steps": cfg.num_inference_steps,
                "num_images": 1,
                "enable_safety_checker": True,
            }
            if cfg.negative_prompt:
                payload["negative_prompt"] = cfg.negative_prompt
            
            resp = requests.post(api_url, headers=headers, json=payload, timeout=120)
            step_img_gen.raw_response = resp.text[:2000]
            
            if resp.status_code == 200:
                data = resp.json()
                images = data.get("images") or data.get("output") or []
                if images:
                    img_info = images[0] if isinstance(images, list) else images
                    generated_image_url = img_info.get("url") if isinstance(img_info, dict) else img_info
                    step_img_gen.output_data = {
                        "image_url": generated_image_url,
                        "status_code": resp.status_code,
                    }
                    step_img_gen.finish(success=True)
                else:
                    step_img_gen.finish(success=False, error="No images in response")
            else:
                step_img_gen.finish(success=False, error=f"HTTP {resp.status_code}")
    except Exception as e:
        step_img_gen.finish(success=False, error=f"{type(e).__name__}: {str(e)}")
        step_img_gen.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 11: Telegram Rewriter (runs even if TG sending is off)
    # ============================================================
    step_tg_rewrite = DiagnosticStep(name="11. Telegram Rewriter")
    result.steps.append(step_tg_rewrite)
    step_tg_rewrite.start()
    step_tg_rewrite.input_data = {"title": current_title[:100], "content": current_content[:200] + "..."}
    tg_title = current_title
    tg_content = current_content
    try:
        from .models import TelegramRewriterConfig
        cfg = TelegramRewriterConfig.objects.order_by("-updated_at").first()
        if not cfg or not cfg.is_enabled:
            step_tg_rewrite.output_data = {"note": "Would use content as-is for Telegram"}
            step_tg_rewrite.skip("Telegram rewriter is disabled in admin")
        else:
            from openai import OpenAI
            api_key = getattr(settings, "OPENAI_API_KEY", None)
            base_url = getattr(settings, "OPENAI_BASE_URL", None)
            if not api_key:
                step_tg_rewrite.skip("OpenAI API key not configured")
            else:
                client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)
                system_prompt = cfg.prompt or "Rewrite for Telegram. Return JSON with 'title' and 'content' keys."
                response = client.chat.completions.create(
                    model=cfg.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Title: {current_title}\n\nContent: {current_content}"},
                    ],
                )
                raw = response.choices[0].message.content or ""
                step_tg_rewrite.raw_response = raw[:2000]
                step_tg_rewrite.tokens_used = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
                try:
                    data = json.loads(raw)
                    tg_title = data.get("title", current_title)
                    tg_content = data.get("content", current_content)
                    step_tg_rewrite.output_data = {
                        "title": tg_title[:200],
                        "content": tg_content[:500] + "..." if len(tg_content) > 500 else tg_content,
                        "char_count": len(tg_content),
                    }
                except json.JSONDecodeError:
                    step_tg_rewrite.output_data = {"raw_text": raw[:500], "parse_error": "Could not parse JSON"}
                step_tg_rewrite.finish(success=True)
    except Exception as e:
        step_tg_rewrite.finish(success=False, error=f"{type(e).__name__}: {str(e)}")
        step_tg_rewrite.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 12: Telegram Delivery Test
    # ============================================================
    step_telegram = DiagnosticStep(name="12. Telegram Delivery")
    result.steps.append(step_telegram)
    step_telegram.start()
    try:
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        channel = getattr(settings, "TELEGRAM_CHANNEL", None)
        
        if not bot_token:
            step_telegram.skip("TELEGRAM_BOT_TOKEN not configured")
        elif not channel:
            step_telegram.skip("TELEGRAM_CHANNEL not configured")
        elif not send_to_telegram:
            step_telegram.output_data = {
                "note": "Telegram test skipped (send_to_telegram=False)",
                "bot_token": f"...{bot_token[-8:]}" if bot_token else None,
                "channel": channel,
                "message_preview": tg_content[:200] + "...",
            }
            step_telegram.skip("Test mode - not actually sending")
        else:
            try:
                from telegram import Bot
            except ImportError:
                step_telegram.skip("python-telegram-bot not installed")
                Bot = None
            
            if Bot:
                step_telegram.input_data = {
                    "channel": channel,
                    "message_preview": f"[DIAGNOSTIC TEST] {tg_title[:50]}...",
                }
                bot = Bot(token=bot_token)
                test_message = f"🔧 <b>Diagnostic Test</b>\n\n{tg_title}\n\n{tg_content[:500]}\n\n<i>This is an automated test message. You can delete it.</i>"
                bot.send_message(
                    chat_id=channel,
                    text=test_message[:4096],
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
                step_telegram.output_data = {"sent": True, "message_length": len(test_message)}
                step_telegram.finish(success=True)
    except Exception as e:
        step_telegram.finish(success=False, error=f"{type(e).__name__}: {str(e)}")
        step_telegram.raw_response = traceback.format_exc()[-1000:]
    
    # ============================================================
    # STEP 13: Outbox Status
    # ============================================================
    step_outbox = DiagnosticStep(name="13. Outbox Status")
    result.steps.append(step_outbox)
    step_outbox.start()
    try:
        from .models import OutboxEvent
        from django.db.models import Count
        
        pending = OutboxEvent.objects.filter(delivered_at__isnull=True).count()
        delivered_today = OutboxEvent.objects.filter(
            delivered_at__isnull=False,
            delivered_at__date=timezone.now().date()
        ).count()
        failed = OutboxEvent.objects.filter(
            delivered_at__isnull=True,
            delivery_attempts__gte=3
        ).count()
        
        # Check for duplicates
        dupes = list(OutboxEvent.objects
            .filter(delivered_at__isnull=True, event_type='news.created')
            .values('payload__id')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)[:10])
        
        step_outbox.output_data = {
            "pending_events": pending,
            "delivered_today": delivered_today,
            "failed_events": failed,
            "duplicate_news_ids": [d['payload__id'] for d in dupes] if dupes else [],
        }
        step_outbox.finish(success=True)
    except Exception as e:
        step_outbox.finish(success=False, error=f"{type(e).__name__}: {str(e)}")
    
    # ============================================================
    # STEP 14: Token Usage Summary
    # ============================================================
    step_summary = DiagnosticStep(name="14. Token Usage Summary")
    result.steps.append(step_summary)
    step_summary.start()
    try:
        total_prompt = 0
        total_completion = 0
        by_step = {}
        
        for step in result.steps:
            if step.tokens_used:
                p = step.tokens_used.get("prompt_tokens", 0)
                c = step.tokens_used.get("completion_tokens", 0)
                total_prompt += p
                total_completion += c
                by_step[step.name] = {"prompt": p, "completion": c, "total": p + c}
        
        step_summary.output_data = {
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "by_step": by_step,
            "estimated_cost_usd": round((total_prompt * 0.00001 + total_completion * 0.00003), 4),  # rough GPT-4 estimate
        }
        step_summary.finish(success=True)
    except Exception as e:
        step_summary.finish(success=False, error=str(e))
    
    # Calculate overall status
    result.total_duration_ms = (time.time() - overall_start) * 1000
    statuses = [s.status for s in result.steps]
    if "error" in statuses:
        result.overall_status = "error"
    elif all(s in ("success", "skipped") for s in statuses):
        result.overall_status = "success"
    else:
        result.overall_status = "partial"
    
    return result
