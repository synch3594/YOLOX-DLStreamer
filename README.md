# YOLOX-DLStreamer

Deployed [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) to [DL Streamer](https://github.com/openvinotoolkit/dlstreamer_gst).

<div align="center"><img src="sample.gif"/></div>

# Requirements

[OpenVINO™ System Requirements](https://www.intel.com/content/www/us/en/developer/tools/openvino-toolkit/system-requirements.html)

# Installation

## Build docker image.

```
$ docker build -t yolox_dlstreamer:latest .
```

# Run

## Download model.

Download YOLOX-s OpenVINO format models from the YOLOX repository.

```
$ wget https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s_openvino.tar.gz
$ tar xf yolox_s_openvino.tar.gz
```

## Run pipeline.

```
$ xhost +
$ docker run -it --privileged --net=host \
   --device /dev/dri \
   -v ~/.Xauthority:/home/dlstreamer/.Xauthority \
   -v /tmp/.X11-unix \
   -e DISPLAY=$DISPLAY \
   -v /dev/bus/usb \
   -v ${PWD}:${PWD} -w ${PWD} \
   --rm yolox_dlstreamer:latest \
   python3 python/pipeline.py -i file://${PWD}/sample.mp4 -m yolox_s.xml
```

# Reference

For the license of each software, please refer to the following.

[YOLOX](https://github.com/Megvii-BaseDetection/YOLOX/blob/main/LICENSE)

[DL Streamer](https://github.com/dlstreamer/dlstreamer/blob/master/LICENSE)

The following sample video was borrowed.

https://www.pexels.com/ja-jp/video/853889/
