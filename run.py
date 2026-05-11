import os
# pyrefly: ignore [missing-import]
import uvicorn

from app.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=not settings.is_production,
        log_level=settings.log_level.lower(),
    )
