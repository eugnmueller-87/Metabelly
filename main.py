import uvicorn

from metabelly.core.config import settings


def main() -> None:
    uvicorn.run(
        "metabelly.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
