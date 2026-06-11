FROM continuumio/miniconda3:latest

# Install basic utils
RUN apt-get update && apt-get install -y wget curl bzip2 git libgomp1 procps && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Configure Conda channels
RUN conda config --add channels defaults && \
    conda config --add channels bioconda && \
    conda config --add channels conda-forge

# Install bioinformatics tools (amrfinderplus, rgi, nextflow require java)
RUN conda install -y -c bioconda ncbi-amrfinderplus rgi nextflow
RUN conda install -y -c conda-forge openjdk=11

# Update AMRFinderPlus Database
RUN amrfinder -u || true

# Install CARD database for RGI
RUN mkdir -p /opt/card && cd /opt/card && \
    wget -qO- https://card.mcmaster.ca/latest/data | tar -xj && \
    rgi load --card_json card.json --local || true

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn fastapi celery redis psycopg2-binary alembic requests

# Copy application source
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/conda/bin:$PATH"

EXPOSE 8000
