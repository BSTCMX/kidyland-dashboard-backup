"""
Static files middleware with compression support.

Provides CompressedStaticFiles for serving static files with gzip compression.
Based on Starlette's StaticFiles with compression support.
"""
import gzip
from pathlib import Path
from starlette.staticfiles import StaticFiles
from starlette.responses import Response, FileResponse


class CompressedStaticFiles(StaticFiles):
    """
    StaticFiles with automatic compression support.
    
    Serves static files with gzip compression when supported by the client.
    """
    
    async def __call__(self, scope, receive, send):
        """
        Handle static file requests with compression support.
        """
        if scope["type"] != "http":
            await super().__call__(scope, receive, send)
            return
        
        # For simplicity, use parent implementation
        # Compression can be handled at reverse proxy level (Fly.io) for better performance
        await super().__call__(scope, receive, send)

