ARG BUILD_FROM
FROM ${BUILD_FROM}

# HA base images are Alpine — bashio, s6-overlay, and jq are already installed.
# We only need to add ffmpeg (for RTSP->HLS) and Python.
RUN apk add --no-cache \
        python3 \
        py3-pip \
        ffmpeg \
        gcc \
        musl-dev \
        python3-dev \
        libffi-dev

WORKDIR /app

COPY app/backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /app/backend/requirements.txt

COPY app/ /app/
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]