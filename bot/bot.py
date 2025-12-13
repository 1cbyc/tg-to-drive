"""
Telegram bot for monitoring and controlling the mirror process
"""

import asyncio
import os
from typing import Optional
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from core.config import Config
from core.processor import MirrorProcessor
from core.utils import clean_channel_link


class MirrorBot:
    """Telegram bot for monitoring and controlling mirror operations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.bot: Optional[Client] = None
        self.processor: Optional[MirrorProcessor] = None
        self.is_running = False
        self.current_task: Optional[asyncio.Task] = None
        
    def initialize(self):
        """Initialize the bot client."""
        if not self.config.bot_token:
            raise ValueError("Bot token is required for bot mode")
        
        # Pyrogram requires api_id and api_hash even for bot mode
        if not self.config.api_id or not self.config.api_hash:
            raise ValueError(
                "TELEGRAM_API_ID and TELEGRAM_API_HASH are required for bot mode. "
                "Set them as environment variables."
            )
        
        self.bot = Client(
            "mirror_bot",
            api_id=self.config.api_id,
            api_hash=self.config.api_hash,
            bot_token=self.config.bot_token
        )
        
        # Register handlers
        self._register_handlers()
        
    def _register_handlers(self):
        """Register bot command handlers."""
        
        @self.bot.on_message(filters.command("start") & filters.private)
        async def start_command(client: Client, message: Message):
            """Start command handler."""
            if self.is_running:
                await message.reply_text("⚠️ Mirror process is already running!")
                return
            
            text = (
                "🤖 **Telegram to Drive Mirror Bot**\n\n"
                "Available commands:\n"
                "/mirror - Start mirroring a channel\n"
                "/status - Check current status\n"
                "/stop - Stop current operation\n"
                "/help - Show this help message"
            )
            await message.reply_text(text)
        
        @self.bot.on_message(filters.command("mirror") & filters.private)
        async def mirror_command(client: Client, message: Message):
            """Start mirroring command."""
            if self.is_running:
                await message.reply_text("⚠️ Mirror process is already running!")
                return
            
            # Get channel from command or use configured one
            command_parts = message.text.split()
            channel = self.config.channel_link
            
            if len(command_parts) > 1:
                channel = clean_channel_link(command_parts[1].strip())
            
            if not channel:
                await message.reply_text(
                    "❌ No channel specified!\n\n"
                    "Usage: `/mirror @channelname`\n"
                    "Or set TELEGRAM_CHANNEL environment variable",
                    parse_mode="markdown"
                )
                return
            
            self.config.channel_link = channel
            
            # Start mirroring in background
            await message.reply_text(f"🚀 Starting mirror for {channel}...")
            self.is_running = True
            
            # Create processor and set progress callback
            self.processor = MirrorProcessor(self.config)
            self.processor.set_progress_callback(self._progress_callback)
            
            # Run in background
            self.current_task = asyncio.create_task(self._run_mirror(message))
        
        @self.bot.on_message(filters.command("status") & filters.private)
        async def status_command(client: Client, message: Message):
            """Status command handler."""
            if not self.is_running:
                await message.reply_text("ℹ️ No mirror process running.")
                return
            
            if self.processor:
                stats = (
                    f"📊 **Mirror Status**\n\n"
                    f"✓ Downloaded: {self.processor.downloaded_count}\n"
                    f"⊘ Skipped: {self.processor.skipped_count}\n"
                    f"✗ Failed: {self.processor.failed_count}\n"
                    f"📦 Total Size: {self.processor.total_size / (1024**3):.2f} GB"
                )
                await message.reply_text(stats)
            else:
                await message.reply_text("⏳ Processing...")
        
        @self.bot.on_message(filters.command("stop") & filters.private)
        async def stop_command(client: Client, message: Message):
            """Stop command handler."""
            if not self.is_running:
                await message.reply_text("ℹ️ No mirror process running.")
                return
            
            # Cancel task if running
            if self.current_task:
                self.current_task.cancel()
            
            self.is_running = False
            if self.processor:
                self.processor.cleanup()
            
            await message.reply_text("🛑 Mirror process stopped.")
        
        @self.bot.on_message(filters.command("help") & filters.private)
        async def help_command(client: Client, message: Message):
            """Help command handler."""
            help_text = (
                "📖 **Help - Telegram to Drive Mirror Bot**\n\n"
                "**Commands:**\n"
                "/start - Show welcome message\n"
                "/mirror [@channel] - Start mirroring a channel\n"
                "/status - Check current mirror status\n"
                "/stop - Stop current mirror operation\n"
                "/help - Show this help message\n\n"
                "**Usage:**\n"
                "1. Set your API credentials via environment variables\n"
                "2. Use /mirror @channelname to start\n"
                "3. Monitor progress with /status\n"
                "4. Stop with /stop if needed"
            )
            await message.reply_text(help_text)
    
    async def _progress_callback(self, event: str, **kwargs):
        """Progress callback for processor updates."""
        # This can be used to send progress updates to Telegram
        # For now, we'll just log it
        print(f"[Bot Progress] {event}: {kwargs}")
    
    async def _run_mirror(self, start_message: Message):
        """Run the mirror process."""
        import concurrent.futures
        
        try:
            # Run processor in thread executor since it uses sync Telethon
            loop = asyncio.get_event_loop()
            executor = concurrent.futures.ThreadPoolExecutor()
            
            # Initialize in executor
            init_success = await loop.run_in_executor(
                executor,
                self.processor.initialize
            )
            
            if not init_success:
                await start_message.reply_text("❌ Failed to initialize. Check your configuration.")
                self.is_running = False
                return
            
            # Run processing in executor
            success = await loop.run_in_executor(
                executor,
                self.processor.process_channel
            )
            
            if success:
                await start_message.reply_text(
                    f"✅ Mirror completed!\n\n"
                    f"Downloaded: {self.processor.downloaded_count}\n"
                    f"Skipped: {self.processor.skipped_count}\n"
                    f"Failed: {self.processor.failed_count}"
                )
            else:
                await start_message.reply_text("❌ Mirror process encountered errors.")
            
        except asyncio.CancelledError:
            await start_message.reply_text("🛑 Mirror process was cancelled.")
        except Exception as e:
            await start_message.reply_text(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if self.processor:
                # Cleanup in executor
                loop = asyncio.get_event_loop()
                executor = concurrent.futures.ThreadPoolExecutor()
                await loop.run_in_executor(executor, self.processor.cleanup)
            self.is_running = False
            self.current_task = None
    
    # Note: Bot is started via bot.bot.run() in run_bot.py
    # This method is kept for compatibility but not used
    async def start(self):
        """Start the bot asynchronously (not used - use bot.bot.run() instead)."""
        pass
    
    async def stop(self):
        """Stop the bot."""
        if self.bot:
            await self.bot.stop()

