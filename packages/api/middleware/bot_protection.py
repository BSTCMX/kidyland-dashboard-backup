"""
Bot protection middleware.

Blocks known bots and crawlers to reduce server load and prevent scraping.
"""
import logging
from fastapi import Request, Response

logger = logging.getLogger(__name__)

# List of known bot user agents to block
BOT_USER_AGENTS = [
    "bot", "crawler", "spider", "scraper", "crawling",
    "facebookexternalhit", "facebot", "slurp", "duckduckbot",
    "baiduspider", "yandexbot", "sogou", "exabot", "ia_archiver",
    "msnbot", "bingbot", "discordbot", "twitterbot", "linkedinbot",
    "slackbot", "whatsapp", "telegrambot", "applebot",
    "petalbot", "semrushbot", "ahrefsbot", "dotbot", "mj12bot",
    "megaindex", "rogerbot", "screaming frog", "siteauditbot",
]

# List of known bot IP ranges (optional, can be extended)
BOT_IP_PATTERNS = [
    # Add specific IP ranges if needed
]


async def bot_protection_middleware(request: Request, call_next):
    """
    Middleware to block known bots and crawlers.
    
    Checks user agent and optionally IP address to identify and block bots.
    Returns 403 Forbidden for detected bots.
    """
    user_agent = request.headers.get("user-agent", "").lower()
    
    # Check if user agent matches known bot patterns
    is_bot = any(bot_pattern in user_agent for bot_pattern in BOT_USER_AGENTS)
    
    # Optional: Check IP address patterns (if needed)
    # client_ip = request.client.host if request.client else None
    # is_bot_ip = any(ip_pattern in client_ip for ip_pattern in BOT_IP_PATTERNS) if client_ip else False
    
    if is_bot:
        logger.info(f"Bot blocked: {user_agent[:100]} from {request.client.host if request.client else 'unknown'}")
        return Response(
            status_code=403,
            content="Forbidden",
            headers={"Content-Type": "text/plain"},
        )
    
    # Allow request to continue
    response = await call_next(request)
    return response

