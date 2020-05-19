"""Ring buffer for automatic rolling storage of images as they are
acquired.

"""

import os.path
from datetime import datetime
import numpy as np
import tables
from log import logger


class RingBuffer(object):
    """Buffer for automatic rolling storage of images to disk.

    This utilizes the PyTables module for data persistence. A utility
    :meth:`to_list` method is included for exporting to other arbitrary
    formats. Additionally, several ``save`` methods are defined to
    export to several other formats, with the caveat that they may
    require additional external dependencies. See the relevant
    docstrings for details.

    """
    def __init__(self, **kwargs):
        """Initialize the ring buffer.

        Keyword arguments
        -----------------
        N : int
            Number of images to store in the ring buffer.
        directory : str
            The directory to buffer images to.
        filename : str
            Filename to use for the ring buffer file.
        recording : bool
            Activate recording when True, disable when False.
        roi : list
            The currently selected region of interest.

        """
        directory = kwargs.get('directory', '.')
        filename = kwargs.get('filename', 'rbuffer.h5')
        recording = kwargs.get('recording', True)
        N = int(kwargs.get('N', 100))
        roi = kwargs.get('roi', [10, 100, 10, 100])
        assert isinstance(directory, str)
        assert isinstance(filename, str)
        assert isinstance(recording, (int, bool))
        assert isinstance(roi, (list, tuple, np.ndarray))

        self.recording = recording
        self.N = N
        self.roi = roi
        self._index = 0
        self.filename = os.path.join(directory, filename)
        self.db = tables.open_file(self.filename, 'w', title="Ring Buffer")
        self.db.create_group('/', 'images', 'Buffered Images')

    def __enter__(self):
        return self

    def __exit__(self, type_, value, tb):
        self.close()

    def __len__(self):
        """Return the number of items actually stored in the ring
        buffer.

        """
        return len(self.db.list_nodes('/images'))

    def close(self):
        self.db.close()

    @property
    def index(self):
        return self._index

    def get_current_index(self):
        """Deprecated."""
        return self.index

    def set_recording_state(self, state):
        """Explicitly set the recording state to state."""
        assert isinstance(state, (bool, int))
        self.recording = state

    def toggle(self):
        """Toggle the recording state."""
        if self.recording:
            logger.debug('Pausing ring buffer recording')
        else:
            logger.debug('Resuming ring buffer recording')
        self.recording = not self.recording

    def write(self, data, roi=None):
        """Add the data to the queue to be written to disk.

        TODO: enable compression

        """
        if not self.recording:
            return

        roi = roi or self.roi

        name = 'img{:04d}'.format(self._index)
        try:
            self.db.get_node('/images/' + name).remove()
        except tables.NoSuchNodeError:
            pass
        finally:
            # TODO: Adapt to CArray for compression
            # filters = tables.Filters(complevel=5, complib='zlib')
            arr = self.db.create_array('/images', name, data)
            arr.attrs.timestamp = datetime.strftime(
                datetime.now(), '%Y-%m-%d %H:%M:%S.%f')
            arr.attrs.roi = roi
            arr.flush()
        self.db.flush()

        self._index = self._index + 1 if self._index < self.N - 1 else 0

    def read(self, index):
        """Return data from the ring buffer file."""
        assert type(index) is int
        img = self.db.get_node('/images/img{:04d}'.format(index))
        return np.array(img)

    def get_timestamp(self, index):
        """Return the timestamp associated with the specified image
        index.

        """
        return self.db.get_node(
            '/images/img{:04d}'.format(index)).attrs.timestamp

    def get_roi(self, index):
        """Return the recorded ROI for the given index."""
        return self.db.get_node('/images/img{:04d}'.format(index)).attrs.roi

    def to_list(self):
        """Convert a :class:`RingBuffer` shelf to a list. This is useful
        for examining and exporting images to other formats.

        """
        listified = []
        for i in range(self.N):
            try:
                listified.append(self.read(i))
            except tables.NoSuchNodeError:
                break
        return listified

    def save_as(self, filename):
        """Save the ring buffer to file filename. The output format
        will depend on the extension of filename.

        """
        raise NotImplementedError(
            "Saving ring buffers to other formats is not yet implemented.")

        if filename[-3:] == 'zip':
            pass  # TODO
        elif filename[-2:] == 'h5':
            pass  # TODO
        elif filename[-4:] == 'fits':
            pass  # TODO
        elif filename[-3:] == 'npz':
            self.save_as_numpy(filename)

    def save_as_hdf5(self, filename):
        """Save the ring buffer to an HDF5 file using the PyTables
        library. This requires PyTables to be installed with either
        conda::

          $ conda install pytables

        or pip::

          $ pip install tables

        """

    def save_as_fits(self, filename):
        """Save the ring buffer to a FITS file using the Astropy
        library. This requires Astropy to be installed with either
        conda::

          $ conda install astropy

        of pip::

          $ pip install astropy

        Notes
        -----
        FITS is convenient for browsing a series of images as many
        graphical programs can read them. See for example ImageJ__.

        __ http://imagej.nih.gov/ij/

        """

    def save_as_numpy(self, filename, compressed=False):
        """Save the ring buffer to Numpy's native npz format. If
        ``compressed`` is ``True``, save using :func:`numpy.savez_compressed`
        instead of :func:`numpy.savez`.

        """
        logger.warn(
            'Saving in npz format loses timestamp and ROI information.')
        logger.warn('Consider saving in FITS or HDF5 formats instead.')
        save_func = np.savez_compressed if compressed else np.savez
        save_func(filename, *self.to_list())
