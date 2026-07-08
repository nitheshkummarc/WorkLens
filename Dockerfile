# =============================================================================
# WorkLens — Multi-stage production image
# =============================================================================
# Build:
#   docker build -t worklens .
#
# Run (mount the candidate pool, write the CSV back out):
#   docker run --rm -v "$PWD/data-volume:/data" worklens \
#       --candidates /data/candidates.jsonl --out /data/submission.csv
#
# Accepts candidates.jsonl or candidates.jsonl.gz transparently.
# =============================================================================

# --------------- Stage 1: Builder ---------------
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --------------- Stage 2: Runtime ---------------
FROM python:3.12-slim AS runtime

LABEL maintainer="WorkLens Contributors"
LABEL description="Deterministic candidate ranking engine"

# Copy only the installed packages from the builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application source and committed data artifacts
COPY rank.py .
COPY shared/ shared/
COPY modules/ modules/
COPY data/ data/

# Non-root user for security
RUN useradd --create-home --shell /bin/bash worklens \
    && chown -R worklens:worklens /app
USER worklens

# Health check: verify the entrypoint is importable
HEALTHCHECK --interval=30s --timeout=5s --retries=1 \
    CMD python -c "from shared.config import scoring; print('ok')" || exit 1

ENTRYPOINT ["python", "rank.py"]
CMD ["--candidates", "/data/candidates.jsonl", "--out", "/data/submission.csv"]
