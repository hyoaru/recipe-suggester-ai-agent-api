FROM ghcr.io/astral-sh/uv:python3.12-alpine AS base

# Build stage
FROM base AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /api

COPY \
  pyproject.toml \
  uv.lock \
  .python-version \
  .env \
  main.py \
  /api/

COPY \
  ./app \
  /api/app

RUN --mount=type=cache,target=/root/.cache/uv \ 
  uv sync --no-dev

# Run stage
FROM base AS runner
WORKDIR /api

RUN apk add curl bash && apk cache clean \
  && addgroup -g 1000 nonroot \
  && adduser -u 1000 -G nonroot -S nonroot \
  && touch app.log \
  && chown 1000:1000 app.log

COPY --from=builder --chown=root:root --chmod=755 /api /api
USER nonroot

ENV PATH="/api/.venv/bin:$PATH"

CMD [ "fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000" ]
