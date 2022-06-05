FROM intel/dlstreamer:latest

SHELL ["/bin/bash", "-c"] 
ENV SHELL /bin/bash

ENV DEBIAN_FRONTEND=noninteractive

USER root

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    wget \
    python3 \
    python3-pip \
    python3-dev \
 && apt-get clean all \
 && rm -rf /var/lib/apt/list/*

RUN cd /opt \
 && git clone https://github.com/Megvii-BaseDetection/YOLOX \
 && cd /opt/YOLOX \
 && rm /usr/local/share/man/man1 \
 && pip3 install tifffile==2019.7.26 \
 && pip3 install -r requirements.txt \
 && pip3 install -v -e .
