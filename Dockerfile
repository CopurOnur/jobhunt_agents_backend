# Read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker
# Multi-agent Job Application Flow for HuggingFace Spaces

FROM python:3.12

# Create non-root user for security
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Install dependencies
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code
COPY --chown=user . /app

# Create storage directories
RUN mkdir -p storage/job_postings storage/applications

# Expose port 7860 (HuggingFace Spaces standard)
EXPOSE 7860

# Run the FastAPI application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
