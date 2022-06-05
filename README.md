# YOLOX-dlstreamer

Deployed [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) to [DL Streamer](https://github.com/openvinotoolkit/dlstreamer_gst).

<div align="center"><img src="sample.gif"/></div>

# Installation

## Build docker image.

```
$ docker build -t yolox_dlstreamer:latest .
```

# Run

## Download OpenVINO models.

```
# Download YOLOX-s OpenVINO format models from the YOLOX repository
$ wget https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s_openvino.tar.gz
$ tar xf yolox_s_openvino.tar.gz
```

## Run pipeline.

```
$ docker run -it --privileged --net=host \
   --device /dev/dri \
   -v ~/.Xauthority:/home/dlstreamer/.Xauthority \
   -v /tmp/.X11-unix \
   -e DISPLAY=$DISPLAY \
   -v /dev/bus/usb \
   -v ${PWD}:/${PWD} -w ${PWD} \
   --rm yolox_dlstreamer:latest \
   python3 python/pipeline.py -i file://${PWD}/sample.mp4 -m yolox_s.xml
```

# License

This software includes the work that is distributed in the Apache License 2.0.
