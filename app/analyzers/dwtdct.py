"""DWT-DCT 'invisible-watermark' (ShieldMnt, MIT), faithful port of EmbedMaxDct so we do not need the
package's torch/onnx dependencies. Byte-for-byte compatible with the `dwtDct` method used by the
Stable Diffusion reference scripts ("StableDiffusionV1") and diffusers' SDXL watermarker (48-bit pattern).

Scheme (per channel with scale > 0; default scales=[0,36,0] -> U channel only):
  BGR -> YUV ; 1-level Haar DWT ; LL band split into 4x4 blocks ; in each block the largest-magnitude
  AC coefficient is quantised (QIM) so that (|v| mod scale) falls in the upper half for bit 1, lower half for bit 0.
Decoding averages the per-block votes for each bit position (bits are tiled across all blocks).
"""
from __future__ import annotations

import numpy as np

try:
    import cv2
    import pywt
    HAVE_DEPS = True
except Exception:  # pragma: no cover
    HAVE_DEPS = False


class EmbedMaxDct:
    def __init__(self, watermarks=None, wmLen=8, scales=(0, 36, 0), block=4):
        self._watermarks = list(watermarks or [])
        self._wmLen = wmLen
        self._scales = list(scales)
        self._block = block

    def encode(self, bgr):
        (row, col, _) = bgr.shape
        yuv = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)
        for channel in range(2):
            if self._scales[channel] <= 0:
                continue
            ca1, (h1, v1, d1) = pywt.dwt2(yuv[:row // 4 * 4, :col // 4 * 4, channel], "haar")
            self.encode_frame(ca1, self._scales[channel])
            yuv[:row // 4 * 4, :col // 4 * 4, channel] = pywt.idwt2((ca1, (v1, h1, d1)), "haar")
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

    def decode(self, bgr):
        (row, col, _) = bgr.shape
        yuv = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)
        scores = [[] for _ in range(self._wmLen)]
        for channel in range(2):
            if self._scales[channel] <= 0:
                continue
            ca1, _ = pywt.dwt2(yuv[:row // 4 * 4, :col // 4 * 4, channel], "haar")
            scores = self.decode_frame(ca1, self._scales[channel], scores)
        avg = np.array([np.array(s).mean() if s else 0.5 for s in scores])
        bits = (avg * 255 > 127)
        return bits, avg

    def decode_frame(self, frame, scale, scores):
        (row, col) = frame.shape
        num = 0
        b = self._block
        for i in range(row // b):
            for j in range(col // b):
                block = frame[i * b:i * b + b, j * b:j * b + b]
                scores[num % self._wmLen].append(self.infer_dct_matrix(block, scale))
                num += 1
        return scores

    def encode_frame(self, frame, scale):
        (row, col) = frame.shape
        num = 0
        b = self._block
        for i in range(row // b):
            for j in range(col // b):
                block = frame[i * b:i * b + b, j * b:j * b + b]
                wm_bit = self._watermarks[num % self._wmLen]
                frame[i * b:i * b + b, j * b:j * b + b] = self.diffuse_dct_matrix(block, wm_bit, scale)
                num += 1
        return frame

    def diffuse_dct_matrix(self, block, wm_bit, scale):
        pos = np.argmax(abs(block.flatten()[1:])) + 1
        i, j = pos // self._block, pos % self._block
        val = block[i][j]
        if val >= 0.0:
            block[i][j] = (val // scale + 0.25 + 0.5 * wm_bit) * scale
        else:
            val = abs(val)
            block[i][j] = -1.0 * (val // scale + 0.25 + 0.5 * wm_bit) * scale
        return block

    def infer_dct_matrix(self, block, scale):
        pos = np.argmax(abs(block.flatten()[1:])) + 1
        i, j = pos // self._block, pos % self._block
        val = abs(block[i][j])
        return 1 if (val % scale) > 0.5 * scale else 0


def embed_bits(bgr: np.ndarray, bits: list[int], scales=(0, 36, 0)) -> np.ndarray:
    return EmbedMaxDct(bits, wmLen=len(bits), scales=scales).encode(bgr)


def decode_bits(bgr: np.ndarray, n_bits: int, scales=(0, 36, 0)):
    return EmbedMaxDct([], wmLen=n_bits, scales=scales).decode(bgr)
