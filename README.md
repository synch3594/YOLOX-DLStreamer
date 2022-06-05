# YOLOX-dlstreamer

Deployed [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) to [DL Streamer](https://github.com/openvinotoolkit/dlstreamer_gst).

<div align="center"><img src="sample.gif"/></div>

# Installation

## 1. Install OpenVINO

see. [OpenVINO Installation](https://docs.openvinotoolkit.org/latest/openvino_docs_install_guides_installing_openvino_linux.html)

## 2. Install YOLOX

see. [YOLOX Installation](https://github.com/Megvii-BaseDetection/YOLOX#quick-start)

# Run

Setup the OpenVINO environment beforehand.

```
source /opt/intel/openvino_2021/bin/setupvars.sh
```

Run pipeline.

```
python3 pipeline.py -i file:///path/to/input.mp4 -m /path/to/yolox_s.xml
```

# License

This software includes the work that is distributed in the Apache License 2.0.
