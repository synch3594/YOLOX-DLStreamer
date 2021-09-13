import sys
import argparse
import numpy as np

# Gstreamer
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# DL Streamer
import gstgva

# YOLOX
from yolox.data.data_augment import preproc as preprocess
from yolox.data.datasets import COCO_CLASSES
from yolox.utils import mkdir, multiclass_nms, demo_postprocess, vis

class Pipeline:
    def __init__(self, uri, model, input_size=(640, 640), device='CPU'):
        self.input_size = input_size

        Gst.init(None)

        self.pipeline = Gst.Pipeline()
        assert self.pipeline, 'Unable to create pipeline.'

        self.src = self._create_source_bin(uri)
        assert self.src, 'Unable to create uridecodebin.'

        self.conv = Gst.ElementFactory.make('videoconvert', 'videoconvert')
        assert self.conv, 'Unable to create videoconvert.'

        self.infer = Gst.ElementFactory.make('gvainference', 'gvainference')
        assert self.infer, 'Unable to create gvainference.'

        self.conv2 = Gst.ElementFactory.make('videoconvert', 'videoconvert2')
        assert self.conv, 'Unable to create videoconvert2.'

        self.mark = Gst.ElementFactory.make('gvawatermark', 'gvawatermark')
        assert self.mark, 'Unable to create gvawatermark.'

        self.sink = Gst.ElementFactory.make('ximagesink', 'ximagesink')
        assert self.sink, 'Unable to create ximagesink.'

        self.pipeline.add(self.src, self.conv, self.infer, self.conv2, self.mark, self.sink)

        self.infer.set_property('model', model)
        self.infer.set_property('device', device)
        self.sink.set_property('sync', 0)

        srcpad = self.src.get_static_pad("src")
        assert srcpad, 'Unable to create srcpad.'
        sinkpad = self.conv.get_static_pad("sink")
        assert sinkpad, 'Unable to create sinkpad.'
        srcpad.link(sinkpad)
       
        self.conv.link(self.infer)
        self.infer.link(self.conv2)
        self.conv2.link(self.mark)
        self.mark.link(self.sink)

        srcpad = self.infer.get_static_pad('src')
        assert srcpad, 'Unable to create srcpad.'
        srcpad.add_probe(Gst.PadProbeType.BUFFER, self._infer_src_pad_buffer_probe, 0)

    def run(self):
        loop = GLib.MainLoop()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._bus_call, loop)

        sys.stdout.write('Starting pipeline.')
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            loop.run()
        except:
            pass
        self.pipeline.set_state(Gst.State.NULL)

    def _cb_newpad(self, bin, pad, data):
        source_bin = data
        bin_ghost_pad = source_bin.get_static_pad('src')
        if not bin_ghost_pad.set_target(pad):
            sys.stderr.write('Unable to create ghost pad.')

    def _bus_call(self, bus, message, loop):
        if message.type == Gst.MessageType.EOS:
            sys.stdout.write('End of stream.')
            loop.quit()
        elif message.type == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            sys.stderr.write('Stream warning: %s: %s\n' % (err, debug))
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            sys.stderr.write('Stream error: %s: %s\n' % (err, debug))
            loop.quit()
        
        return True

    def _create_source_bin(self, uri):
        src_bin = Gst.Bin.new('source_bin')

        uridecodebin = Gst.ElementFactory.make("uridecodebin", "uridecodebin")
        assert uridecodebin, 'Unable to create uridecodebin.'
        uridecodebin.set_property("uri", uri)
        uridecodebin.connect('pad-added', self._cb_newpad, src_bin)
        
        Gst.Bin.add(src_bin, uridecodebin)
        bin_pad = src_bin.add_pad(Gst.GhostPad.new_no_target('src', Gst.PadDirection.SRC))
        assert bin_pad, 'Unable to create bin_pad.'
        
        return src_bin

    def _infer_src_pad_buffer_probe(self, pad, info, data):
        """
          The implementation of this post-processing is based on the YOLOX demo application.
          https://github.com/Megvii-BaseDetection/YOLOX/tree/main/demo/OpenVINO
        """
        with gstgva.util.GST_PAD_PROBE_INFO_BUFFER(info) as buffer:
            frame = gstgva.VideoFrame(buffer)
            scale_y = self.input_size[0] / frame.video_info().height
            scale_x = self.input_size[1] / frame.video_info().width
            
            clamp_y = lambda y: min(frame.video_info().height, max(y, 0))
            clamp_x = lambda x: min(frame.video_info().width, max(x, 0))

            tensors = frame.tensors()
            for t in tensors:
                data = t.data().reshape(t.dims())

                predictions = demo_postprocess(data, self.input_size, p6=False)[0]
        
                boxes = predictions[:, :4]
                scores = predictions[:, 4, None] * predictions[:, 5:]

                boxes_xyxy = np.ones_like(boxes)
                boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2]/2.
                boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3]/2.
                boxes_xyxy[:, 2] = boxes[:, 0] + boxes[:, 2]/2.
                boxes_xyxy[:, 3] = boxes[:, 1] + boxes[:, 3]/2.

                dets = multiclass_nms(boxes_xyxy, scores, nms_thr=0.45, score_thr=0.1)

                if dets is not None:
                    final_boxes = dets[:, :4]
                    final_scores, final_cls_inds = dets[:, 4], dets[:, 5]

                    for xyxy, score, idx in zip(final_boxes, final_scores, final_cls_inds):
                        xmin = clamp_x(xyxy[0] / scale_x)
                        ymin = clamp_y(xyxy[1] / scale_y)
                        xmax = clamp_x(xyxy[2] / scale_x)
                        ymax = clamp_y(xyxy[3] / scale_y)
                        frame.add_region(xmin, ymin, (xmax - xmin), (ymax - ymin), label=COCO_CLASSES[int(idx)], confidence=score)

        return Gst.PadProbeReturn.OK

def parse_args():
    parser = argparse.ArgumentParser()
    args = parser.add_argument_group('Options')
    args.add_argument(
        '-i',
        '--input',
        required=True,
        type=str,
        help='Required. Input URI.')
    args.add_argument(
        '-m',
        '--model',
        required=True,
        type=str,
        help='Required. Path to model.')
    args.add_argument(
        '--net_w',
        default=640,
        type=int,
        help='Network input width.')
    args.add_argument(
        '--net_h',
        default=640,
        type=int,
        help='Network input height.')
    args.add_argument(
        '-d',
        '--device',
        default='CPU',
        type=str,
        help='Execution device.')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    pipeline = Pipeline(args.input, args.model, (args.net_h, args.net_w), args.device)
    pipeline.run()