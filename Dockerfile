# Stage-3 reproduction image. Builds and runs unmodified, satisfying the
# CPU-only / no-network ranking constraints. Doubles as the `docker run` sandbox
# recipe (submission_spec §10.5 / §125).
#
# Build:
#   docker build -t worklens-redrob .
# Run (mount the candidate pool, write the CSV back out):
#   docker run --rm -v "$PWD":/data worklens-redrob \
#       --candidates /data/candidates.jsonl --out /data/submission.csv
#
# Accepts candidates.jsonl or candidates.jsonl.gz.

FROM python:3.12-slim

WORKDIR /app

# Dependencies first (only pydantic is needed at ranking time) for layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source + committed data artifacts (ontology + JD rubric). No precomputation.
COPY . .

ENTRYPOINT ["python", "rank.py"]
CMD ["--candidates", "/data/candidates.jsonl", "--out", "/data/submission.csv"]
