"""Factory and channel implementation for DingTalk richtext plugin."""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from loguru import logger

from nanobot.bus.queue import MessageBus
from nanobot.channels.dingtalk import (
    DINGTALK_AVAILABLE,
    CallbackHandler,
    DingTalkChannel,
)
from nanobot.config.schema import Config, DingTalkConfig

if DINGTALK_AVAILABLE:
    from dingtalk_stream import AckMessage, CallbackMessage, Credential, DingTalkStreamClient
    from dingtalk_stream.chatbot import ChatbotMessage
else:
    AckMessage = None
    CallbackMessage = None
    Credential = None
    DingTalkStreamClient = None
    ChatbotMessage = None


def _ack_ok(status: str = "OK") -> tuple[Any, str]:
    if AckMessage is None:
        return status, status
    return AckMessage.STATUS_OK, status


class RichTextDingTalkHandler(CallbackHandler):
    """Callback handler that supports rich text and downloads inbound attachments."""

    def __init__(self, channel: "DingTalkRichTextChannel"):
        super().__init__()
        self.channel = channel

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        text = (payload.get("text") or {}).get("content", "").strip()
        if text:
            return text

        content = payload.get("content") or {}
        simple_text = str(content.get("text") or "").strip()
        if simple_text:
            return simple_text

        rich = content.get("richText") or content.get("richtext") or payload.get("richText")
        if isinstance(rich, str):
            return rich.strip()

        chunks: list[str] = []
        if isinstance(rich, dict):
            rich = rich.get("nodes") or rich.get("elements") or rich.get("content")

        if isinstance(rich, list):
            for node in rich:
                if isinstance(node, str):
                    chunks.append(node)
                    continue
                if not isinstance(node, dict):
                    continue
                if node.get("text"):
                    chunks.append(str(node["text"]))
                elif node.get("content") and isinstance(node["content"], str):
                    chunks.append(node["content"])
                elif node.get("children") and isinstance(node["children"], list):
                    for child in node["children"]:
                        if isinstance(child, dict) and child.get("text"):
                            chunks.append(str(child["text"]))

        return "\n".join(s.strip() for s in chunks if s and s.strip()).strip()

    @staticmethod
    def _extract_attachments(payload: dict[str, Any]) -> list[tuple[str, str | None]]:
        result: list[tuple[str, str | None]] = []

        def _push(item: dict[str, Any]) -> None:
            url = item.get("downloadUrl") or item.get("url") or item.get("download_url")
            name = item.get("fileName") or item.get("name")
            if isinstance(url, str) and url:
                result.append((url, str(name) if name else None))

        attachments = payload.get("attachments")
        if isinstance(attachments, list):
            for item in attachments:
                if isinstance(item, dict):
                    _push(item)

        content = payload.get("content")
        if isinstance(content, dict):
            files = content.get("files") or content.get("attachments")
            if isinstance(files, list):
                for item in files:
                    if isinstance(item, dict):
                        _push(item)

        return result

    async def process(self, message: Any):
        try:
            payload: dict[str, Any] = message.data or {}
            sender_id = str(payload.get("senderStaffId") or payload.get("senderId") or "")
            sender_name = str(payload.get("senderNick") or payload.get("senderName") or "Unknown")
            conversation_type = payload.get("conversationType")
            conversation_id = payload.get("conversationId") or payload.get("openConversationId")

            text = self._extract_text(payload)
            files = self._extract_attachments(payload)

            local_media: list[str] = []
            for url, name in files:
                local_path = await self.channel.download_to_tmp(url, preferred_name=name)
                if local_path:
                    local_media.append(local_path)

            if not text and not local_media:
                logger.warning("DingTalk richtext plugin received unsupported empty message")
                return _ack_ok("OK")

            await self.channel.on_inbound(
                content=text,
                sender_id=sender_id,
                sender_name=sender_name,
                conversation_type=conversation_type,
                conversation_id=conversation_id,
                media=local_media,
                raw_payload=payload,
            )

            return _ack_ok("OK")
        except Exception as exc:
            logger.error("DingTalk richtext plugin handler failed: {}", exc)
            return _ack_ok("Error")


class DingTalkRichTextChannel(DingTalkChannel):
    """DingTalk plugin channel with richtext parsing and /tmp attachment download."""

    name = "dingtalk_richtext"
    display_name = "DingTalk RichText"

    def __init__(self, config: DingTalkConfig, bus: MessageBus, download_dir: str = "/tmp"):
        super().__init__(config, bus)
        self._download_dir = Path(download_dir)

    async def start(self) -> None:
        if not DINGTALK_AVAILABLE:
            logger.error("DingTalk Stream SDK not installed. Run: pip install dingtalk-stream")
            return
        if not self.config.client_id or not self.config.client_secret:
            logger.error("DingTalk client_id and client_secret not configured")
            return

        self._running = True
        self._download_dir.mkdir(parents=True, exist_ok=True)

        import httpx

        self._http = httpx.AsyncClient()

        logger.info("Initializing DingTalk richtext plugin with Client ID: {}...", self.config.client_id)
        credential = Credential(self.config.client_id, self.config.client_secret)
        self._client = DingTalkStreamClient(credential)
        self._client.register_callback_handler(ChatbotMessage.TOPIC, RichTextDingTalkHandler(self))

        logger.info("DingTalk richtext plugin channel started")

        while self._running:
            try:
                await self._client.start()
            except Exception as exc:
                logger.warning("DingTalk richtext stream error: {}", exc)
            if self._running:
                logger.info("Reconnecting DingTalk richtext stream in 5 seconds...")
                await asyncio.sleep(5)

    async def download_to_tmp(self, url: str, preferred_name: str | None = None) -> str | None:
        if not self._http:
            return None
        try:
            resp = await self._http.get(url, follow_redirects=True)
            if resp.status_code >= 400:
                logger.warning("DingTalk attachment download failed status={} url={}", resp.status_code, url)
                return None

            parsed = urlparse(url)
            filename = preferred_name or os.path.basename(parsed.path) or "attachment.bin"
            target = self._download_dir / filename
            if target.exists():
                stem = target.stem
                suffix = target.suffix
                target = self._download_dir / f"{stem}-{int(time.time())}{suffix}"

            await asyncio.to_thread(target.write_bytes, resp.content)
            logger.info("DingTalk attachment downloaded to {}", target)
            return str(target)
        except Exception as exc:
            logger.error("DingTalk attachment download error url={} err={}", url, exc)
            return None

    async def on_inbound(
        self,
        *,
        content: str,
        sender_id: str,
        sender_name: str,
        conversation_type: str | None,
        conversation_id: str | None,
        media: list[str],
        raw_payload: dict[str, Any],
    ) -> None:
        is_group = conversation_type == "2" and conversation_id
        chat_id = f"group:{conversation_id}" if is_group else sender_id
        inbound_text = content.strip() if content.strip() else "[Attachment message]"

        await self._handle_message(
            sender_id=sender_id,
            chat_id=chat_id,
            content=inbound_text,
            media=media,
            metadata={
                "sender_name": sender_name,
                "platform": "dingtalk",
                "conversation_type": conversation_type,
                "richtext_enabled": True,
                "raw": raw_payload,
            },
        )


def create_channel(
    *,
    config: Config,
    bus: MessageBus,
    channel_name: str,
    app_config: dict[str, Any],
) -> DingTalkRichTextChannel:
    """Entry point factory for nanobot.channel_factories."""
    del config, channel_name

    plugin_download_dir = str(app_config.get("downloadDir") or "/tmp")
    dingtalk_cfg = DingTalkConfig.model_validate(app_config)
    return DingTalkRichTextChannel(dingtalk_cfg, bus, download_dir=plugin_download_dir)
