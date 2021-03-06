"""
diffusion.py

Colour points diffuse through the grid.
"""

import logging
import numpy as np
import scipy
import scipy.ndimage
import scipy.signal
from ..pattern import Pattern, register_pattern
from colorsys import hsv_to_rgb, rgb_to_hsv
from numpy.random import randint
import sys

logger = logging.getLogger(__name__)


@register_pattern("[COLOUR] Diffusion")
class Sample(Pattern):
    def __init__(self, cfg, tracking):
        logger.info("Diffusion pattern starting up")
        self.grid = np.zeros((7, 7, 3), dtype=int)
        self.n_points = 3
        self.sigma = 0.4
        n = int(np.ceil(np.sqrt(2 * self.sigma**2 * np.log(1000))))
        if n % 2 == 0:
            n = n + 1
        impulse = np.zeros((n, n))
        impulse[int(n//2), int(n//2)] = 1.0
        self.kernel = scipy.ndimage.filters.gaussian_filter(impulse,
                      (self.sigma, self.sigma))
        # Normalise the kernel - the discretisation loses us a lot of the
        # energy very quickly:
        self.kernel /= np.sum(self.kernel)

    def drop(self):
        rgb = hsv_to_rgb(np.random.random(), 1.0, 1.0)
        self.grid[randint(5)+1, randint(5)+1] = [int(x*255) for x in rgb]

    def diffuse(self):
        # Generate a gaussian kernel by gaussian filtering a Dirac Delta
        # Find how big the gaussian needs to be for 1/1000 magnitude at
        # truncation.  We need this n to be odd so that we can place the
        # impulse precisely in the middle.
        self.grid[:, :, 0] = scipy.signal.convolve2d(self.grid[:, :, 0],
                             self.kernel, mode="same", boundary="fill",
                             fillvalue=0)
        self.grid[:, :, 1] = scipy.signal.convolve2d(self.grid[:, :, 1],
                             self.kernel, mode="same", boundary="fill",
                             fillvalue=0)
        self.grid[:, :, 2] = scipy.signal.convolve2d(self.grid[:, :, 2],
                             self.kernel, mode="same", boundary="fill",
                             fillvalue=0)

    def update(self):
        self.diffuse()
        if np.random.random() < 0.05:
            self.drop()

        maxgrid = np.zeros((7, 7, 3), dtype=np.uint8)
        maxgrid += 255
        truncated = np.zeros((7, 7, 6), dtype=np.uint8)
        truncated[:, :, :3] = np.minimum(self.grid, maxgrid)
        truncated[:, :, 3] = 1 # sine
        # Frequency depends on hue of colour:
        for x in range(7):
            for y in range(7):
                colour = truncated[x, y, :3]
                hue = rgb_to_hsv(*[x/255 for x in colour])[0]*255/2
                truncated[x, y, 4] = 100 + hue
        vol = np.zeros((7, 7))
        vol = np.amax(truncated[:, :, 0:3], axis=2)
        vol[vol > 255] = 255
        truncated[:, :, 5] = vol
        return truncated, 1.0/30
