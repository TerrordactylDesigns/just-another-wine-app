ARG BUILD_FROM
FROM ${BUILD_FROM:-python:3.14-slim}

# ffmpeg required for RTSP -> HLS transcoding
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg bash curl && \
    rm -rf /var/lib/apt/lists/*

# bashio for reading Home Assistant add-on options
RUN curl -J -L -o /tmp/bashio.tar.gz \
      "https://github.com/hassio-addons/bashio/archive/v0.16.2.tar.gz" && \
    mkdir -p /tmp/bashio && \
    tar zxvf /tmp/bashio.tar.gz --strip-components 1 -C /tmp/bashio && \
    mv /tmp/bashio/lib /usr/lib/bashio && \
    ln -s /usr/lib/bashio/bashio /usr/bin/bashio && \
    rm -rf /tmp/bashio /tmp/bashio.tar.gz

WORKDIR /app

COPY app/backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY app/ /app/
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
