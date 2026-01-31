"""Diagnostic utilities for testing the full news aggregator pipeline.

Provides detailed logging and step-by-step verification of:
- AI rewriting
- Translation (EN→RU)
- Image generation (OpenAI prompt + fal-ai)
- Telegram delivery
"""
from __future__ import annotations

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
    """Run a full diagnostic of all pipeline components.
    
    Args:
        test_title: Sample article title for testing
        test_content: Sample article content for testing
        send_to_telegram: If True, actually sends a test message to Telegram
        
    Returns:
        DiagnosticResult with detailed step-by-step information
    """
    result = DiagnosticResult()
    result.started_at = timezone.now().isoformat()
    overall_start = time.time()
    
    # Step 1: Check configuration
    step_config = DiagnosticStep(name="Configuration Check")
    result.steps.append(step_config)
    step_config.start()
    try:
        config_info = {
            "OPENAI_API_KEY": "✓ Set" if getattr(settings, "OPENAI_API_KEY", None) else "✗ Missing",
            "OPENAI_BASE_URL": getattr(settings, "OPENAI_BASE_URL", None) or "(default)",
            "TELEGRAM_BOT_TOKEN": "✓ Set" if getattr(settings, "TELEGRAM_BOT_TOKEN", None) else "✗ Missing",
            "TELEGRAM_CHANNEL": getattr(settings, "TELEGRAM_CHANNEL", None) or "✗ Missing",
            "PUBLIC_BASE_URL": getattr(settings, "PUBLIC_BASE_URL", None) or "(not set)",
            "MEDIA_ROOT": str(getattr(settings, "MEDIA_ROOT", "")),
        }
        step_config.output_data = config_info
        step_config.finish(success=True)
    except Exception as e:
        step_config.finish(success=False, error=str(e))
    
    # Step 2: Test Rewriter
    step_rewrite = DiagnosticStep(name="AI Rewriter")
    result.steps.append(step_rewrite)
    step_rewrite.start()
    step_rewrite.input_data = {"title": test_title[:100], "content": test_content[:200] + "..."}
    rewritten_title = test_title
    rewritten_content = test_content
    try:
        from .models import RewriterConfig
        cfg = RewriterConfig.objects.order_by("-updated_at").first()
        if not cfg or not cfg.is_enabled:
            step_rewrite.skip("Rewriter is disabled in admin")
        else:
            from openai import OpenAI
            api_key = getattr(settings, "OPENAI_API_KEY", None)
            base_url = getattr(settings, "OPENAI_BASE_URL", None)
            if not api_key:
                step_rewrite.skip("OpenAI API key not configured")
            else:
                client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)
                # Use prompt as-is (don't use .format() as it may contain literal braces)
                system_prompt = cfg.prompt or "Rewrite this article professionally. Return JSON with 'title' and 'content' keys."
                response = client.chat.completions.create(
                    model=cfg.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Title: {test_title}\n\nContent: {test_content}"},
                    ],
                )
                raw = response.choices[0].message.content or ""
                step_rewrite.raw_response = raw[:2000]
                step_rewrite.tokens_used = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
                # Try to parse JSON response
                try:
                    import json
                    data = json.loads(raw)
                    rewritten_title = data.get("title", test_title)
                    rewritten_content = data.get("content", test_content)
                    step_rewrite.output_data = {
                        "title": rewritten_title[:200],
                        "content": rewritten_content[:500] + "..." if len(rewritten_content) > 500 else rewritten_content,
                    }
                except json.JSONDecodeError:
                    step_rewrite.output_data = {"raw_text": raw[:500]}
                step_rewrite.finish(success=True)
    except Exception as e:
        step_rewrite.finish(success=False, error=f"{type(e).__name__}: {str(e)}")
        step_rewrite.raw_response = traceback.format_exc()[-1000:]
    
    # Step 3: Test Translator
    step_translate = DiagnosticStep(name="EN→RU Translator")
    result.steps.append(step_translate)
    step_translate.start()
    step_translate.input_data = {"title": rewritten_title[:100], "content": rewritten_content[:200] + "..."}
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
                        {"role": "user", "content": f"Title: {rewritten_title}\n\nContent: {rewritten_content}"},
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
                    import json
                    data = json.loads(raw)
                    step_translate.output_data = {
                        "title_ru": data.get("title_ru", "")[:200],
                        "content_ru": (data.get("content_ru", "")[:500] + "...") if len(data.get("content_ru", "")) > 500 else data.get("content_ru", ""),
                    }
                except json.JSONDecodeError:
                    step_translate.output_data = {"raw_text": raw[:500]}
                step_translate.finish(success=True)
    except Exception as e:
        step_translate.finish(success=False, error=f"{type(e).__name__}: {str(e)}")
        step_translate.raw_response = traceback.format_exc()[-1000:]
    
    # Step 4: Test Image Prompt Generation
    step_img_prompt = DiagnosticStep(name="Image Prompt Generation (OpenAI)")
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
                    "title": rewritten_title[:100],
                }
                client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)
                system_prompt = cfg.prompt_generator_instructions or "Generate an image prompt for this article."
                response = client.chat.completions.create(
                    model=cfg.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Article Title: {rewritten_title}\n\nArticle Content: {rewritten_content[:1000]}"},
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
    
    # Step 5: Test Image Generation (fal-ai)
    step_img_gen = DiagnosticStep(name="Image Generation (fal-ai)")
    result.steps.append(step_img_gen)
    step_img_gen.start()
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
            
            # Map aspect ratio to dimensions
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
                    img_url = img_info.get("url") if isinstance(img_info, dict) else img_info
                    step_img_gen.output_data = {
                        "image_url": img_url,
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
    
    # Step 6: Test Telegram Delivery
    step_telegram = DiagnosticStep(name="Telegram Delivery")
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
                    "message_preview": f"[DIAGNOSTIC TEST] {rewritten_title[:50]}...",
                }
                bot = Bot(token=bot_token)
                test_message = f"🔧 <b>Diagnostic Test</b>\n\n{rewritten_title}\n\n<i>This is an automated test message. You can delete it.</i>"
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
    
    # Step 7: Check Outbox Status
    step_outbox = DiagnosticStep(name="Outbox Status")
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
