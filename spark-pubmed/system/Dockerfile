# SPARK Task 1 system image (spark_t1.py 0.1.0).
# MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
#
# NOT BUILT OR RUN YET (2026-10-24): this is the planned image; see README.md "Status".
#
# Build from spark-pubmed/ (so t1_runner/ and rerank/ are in the context), after fetching the
# MedCPT cross-encoder files into system/model/ (rerank/fetch_model.py fetches and checks them;
# the model is public domain, from NCBI, and is not stored in the repository):
#   docker build -f system/Dockerfile -t spark-t1 .
# Run with no network. The FTS5 index that t1_runner/build_index.py writes (about 92.5 GB) is
# mounted at /index; its folder must be writable because the index uses SQLite's WAL journal:
#   docker run --rm --network none -v /path/to/index:/index -v "$PWD/io":/io spark-t1 \
#     --questions /io/questions.jsonl --out-dir /io/out --team-id TEAM
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
RUN pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir numpy==2.1.3 transformers==4.46.3
WORKDIR /app
COPY t1_runner/t1.py t1_runner/build_index.py rerank/rerank.py rerank/rerank_run.py system/spark_t1.py /app/
COPY system/model/ /app/model/
ENTRYPOINT ["python", "/app/spark_t1.py", "--db", "/index/spark_full.db", "--model-dir", "/app/model"]
CMD ["--questions", "/io/questions.jsonl", "--out-dir", "/io/out"]
