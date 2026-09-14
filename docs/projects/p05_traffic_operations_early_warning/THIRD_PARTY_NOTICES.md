# Project 6 — Third-party dependency notices

This records the selected runtime packages, not a detector license approval.
No detector or model weights have been selected, acquired or redistributed.
Model licensing remains unresolved and must be reviewed separately before Step 5.

## OpenCV-headless 5.0.0.93

The selected opencv-python-headless wheels declare Apache 2.0 metadata. Their
Python packaging license (`cv2/LICENSE.txt`) is MIT, copyright Olli-Pekka Heinisuo.
The bundled OpenCV binary notices identify Apache 2.0 for upstream OpenCV.
These are distinct components; a single metadata label does not replace the
packaging and bundled binary licenses.

References: [OpenCV licensing](https://opencv.org/license/) and
[Python packaging license](https://github.com/opencv/opencv-python/blob/master/LICENSE.txt).

The actual Windows/Linux wheels include `cv2/LICENSE-3RD-PARTY.txt` and dist-info
license copies. Full bundled notices include third-party terms such as FFmpeg LGPL,
libvpx, bzip2, OpenSSL, libpng, zlib and libwebp notices. Some notices address other
platforms or build variants; their inclusion alone does not establish that every
listed library, GUI component or codec is present in the selected headless wheel.
Preserve the complete notices with any permitted redistribution and review the
actual distribution/codec use before a later public artifact release.

## ONNX Runtime 1.30.0

The selected CPU onnxruntime wheels include Microsoft's MIT `LICENSE` and
`ThirdPartyNotices.txt`. The latter includes, among others, Intel software and
protobuf terms. Its broad component/provider notices are not proof of installed
CUDA, NVIDIA or Torch Python dependencies; the reviewed dependency closures contain
none of those prohibited Project 6 dependencies.

Reference: [versioned ONNX Runtime license](https://github.com/microsoft/onnxruntime/blob/v1.30.0/LICENSE).

## Review evidence and obligations

Sub-step 2.A downloaded the four actual platform wheels, verified their SHA-256
against resolver artifact metadata, retained their complete notice files, and
verified all six installed notice files per platform against those wheel bytes.
Local unmodified compatibility validation was accepted. This is not blanket approval
for binary redistribution, detector weights or a particular future source video.

Complete filenames, source URLs, hashes, declared licenses, extracted notice members
and notice hashes are in ignored `windows-py313/evidence/wheel-inventory.json` and
`linux-py313/evidence/wheel-inventory.json` under
`.cache/p05_traffic_operations_early_warning/`. Full extracted notices remain beside
the reviewed wheels. These large/local artifacts must not be committed.

The repository already uses imageio-ffmpeg. Its packaged executable has its own
build/license obligations; the runtime resolver's provenance/hash observation is
not a codec redistribution clearance. No FFmpeg binary is copied into Git by 2.B.
Later release review must preserve applicable attributions and notices and determine
what source/media/binary redistribution is actually authorized.


## Block 2 detector and tracking algorithm

YOLOX-Nano official ONNX 0.1.1rc0 release, Megvii-BaseDetection/YOLOX,
Apache-2.0. The exact artifact SHA, provenance, preprocessing and restrictions are
in BLOCK2_REVIEW.md and the ignored detection_manifest.json. Upstream code license:
https://github.com/Megvii-BaseDetection/YOLOX/blob/main/LICENSE
Complete upstream Apache text is retained in YOLOX_LICENSE.txt. Model and source
code are not redistributed in this block. Preprocessing/grid decoding follow the
published interface; source-video publication rights remain separate.

ByteTrack algorithm reference: https://github.com/ifzhang/ByteTrack
Upstream license: MIT, Copyright (c) 2021 Yifu Zhang.
https://github.com/ifzhang/ByteTrack/blob/main/LICENSE
tracking.py is independently written project-local code using the two-stage
association approach; no upstream source file was copied. It changes box-state,
clock handling, confirmation and assignment details and is not an upstream replica.
No ByteTrack package, Torch, Ultralytics or supervision was installed. Preserve the
upstream MIT notice if upstream source is copied in any later authorized change.
