import time
from fastapi import FastAPI, Request
from app.api.routers.recipes import router as router_recipes
from app.api.routers.operations import router as router_operations
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


def create_app():
    load_dotenv()

    app = FastAPI(docs_url="/")
    logger.add(
        "app.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="[{time:YYYY-MM-DD HH:mm:ss}] [{level}] - {message}",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8002",
            "http://localhost:8001",
            "https://hyoaru.github.io/recipe-suggester-ai",
            "https://recipe-ai.anonalyze.org",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s"
        )
        return response

    app.include_router(
        router_recipes,
        prefix="/api",
    )

    app.include_router(
        router_operations,
        prefix="/api/operations",
    )

    return app
