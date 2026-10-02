# WorkLens ranking image.
#
# Build:
#   docker build -t worklens .
#
# Run (mount a directory holding the candidate pool; the CSV is written back to it):
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/data" worklens \
#       --candidates /data/candidates.jsonl --out /data/submission.csv
#
# --user makes the container write as the host user, so the mounted directory
# does not need to be writable by the image's default user. Both .jsonl and
# .jsonl.gz input are accepted.

FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

LABEL description="WorkLens deterministic candidate ranking"

COPY --from=builder /install /usr/local

WORKDIR /app
COPY rank.py .
COPY shared/ shared/
COPY modules/ modules/
COPY data/ data/

RUN useradd --create-home --shell /bin/bash worklens \
    && chown -R worklens:worklens /app
USER worklens

ENTRYPOINT ["python", "rank.py"]
CMD ["--candidates", "/data/candidates.jsonl", "--out", "/data/submission.csv"]
