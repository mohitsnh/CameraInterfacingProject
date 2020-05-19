"""Image manipulation utilities."""

#from __future__ import print_function, division
import numbers
import numpy as np
from matplotlib import cm as mplcm, colors as mplcolors
import PIL.Image

COLORMAPS = sorted([cmap for cmap in mplcm.datad if not cmap.endswith('_r')])


class Image(object):
    """Utility class for representing an image. Images can have
    colormaps applied to them and be transformed in various ways.

    """
    def __init__(self, data, cmap=None, vmin=None, vmax=None):
        """Create a new image from an array.

        Parameters
        ----------
        data : np.ndarray
            Image data as an array
        cmap : str or None
            Name of a matplotlib colormap. If given, immediately apply
            it.
        vmin, vmax : int or float or None
            Colormap minimum and maximum for scaling.

        """
        assert isinstance(data, np.ndarray)
        assert cmap is None or isinstance(cmap, str)
        self.data = data

        self._create_image(cmap, vmin, vmax)

    def _create_image(self, cmap=None, vmin=None, vmax=None):
        """Create a new (PIL) image and optionally apply a
        colormap.

        """
        if cmap:
            self.apply_colormap(cmap, vmin, vmax)
        else:
            # TODO: check that this works properly
            self.img = PIL.Image.fromarray(self.data)

    def apply_colormap(self, cmap=None, vmin=None, vmax=None):
        """Apply a colormap to the image.

        If ``cmap`` is None, use the pre-defined colormap.

        """
        assert cmap is None or isinstance(cmap, str)
        assert vmin is None or isinstance(vmin, numbers.Real)
        assert vmax is None or isinstance(vmax, numbers.Real)
        if vmin is None:
            vmin = self.data.min()
        if vmax is None:
            vmax = self.data.max()
        if cmap is None:
            cmap = self.cmap

        colormap = mplcm.ScalarMappable(
            mplcolors.Normalize(vmin=vmin, vmax=vmax),
            mplcm.get_cmap(str(cmap))
        )
        self.img = PIL.Image.fromarray(
            colormap.to_rgba(self.data, bytes=True))

    def rotate(self, turns):
        """Rotate counterclockwise 90 degrees ``turns`` times."""
        assert type(turns) is int
        self.img = self.img.rotate(90*turns)

    def flip(self, axis):
        """Flip the image either vertically or horizontally.

        Parameters
        ----------
        axis : str
            'vertical' or 'horizontal'

        """
        assert type(axis) is str
        if axis is 'vertical':
            self.img = self.img.transpose(PIL.Image.FLIP_LEFT_RIGHT)
        elif axis is 'horizontal':
            self.img = self.img.transpose(PIL.Image.FLIP_TOP_BOTTOM)

    def tostring(self):
        """Convenience wrapper to the PIL.Image.tostring method."""
        return self.img.tostring()

    def save(self, filename):
        """Save the image to a file."""
        self.img.save(filename)
