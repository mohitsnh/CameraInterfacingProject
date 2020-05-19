"""Thorlabs DCx series cameras

Drivers for Windows and Linux can be downloaded from Thorlabs__.

__ http://www.thorlabs.de/software_pages/viewsoftwarepage.cfm?code=DCx

Python implementation of ueye interface:
__ https://github.com/bernardokyotoku/pydcu

"""
import sys
import ctypes
from ctypes import *
import numpy as np
from camera import Camera


def _chk(msg):
    """Check for errors from the C library."""
    if msg:
        if msg == 127:
            print("Out of memory, probably because of a memory leak!!!")
        if msg == 125:
            print("125: IS_INVALID_PARAMETER: One of the submitted " +
                  "parameters is outside the valid range or is not " +
                  "supported for this sensor or is not available in " +
                  "this mode.")
        if msg == 159:
            print(
                "159: IS_INVALID_BUFFER_SIZE: The image memory has an " +
                "inappropriate size to store the image in the desired format.")
        if msg == 178:
            raise RuntimeError("ThorlabsDCx: Transfer error: 178")
        if msg == 1:
            raise RuntimeError("Invalid camera handle.")
        if msg == -1:
            raise RuntimeError("General error message: Likely the camera was disconnected!")
        print(
            "Unhandled error number: {}. \
            See DCx_User_and_SDK_Manual.pdf for details".format(msg))


# Structures used by the ctypes code:
class ImageFileParams(ctypes.Structure):
    _fields_ = [
        ("pwchFileName", c_wchar_p),
        ("nFileType", c_uint),
        ("nQuality", c_uint),
        ("ppcImageMem;", c_void_p),
        ("pnImageID", c_uint),
        ("reserved", c_byte*32)
    ]


class IS_RECT(ctypes.Structure):
    _fields_ = [
        ("s32x", c_int),
        ("s32y", c_int),
        ("s32Width", c_int),
        ("s32Height", c_int)
    ]


class CamInfo(ctypes.Structure):
    _fields_ = [
        ("SerNo", ctypes.c_char*12),
        ("ID", ctypes.c_char*20),
        ("Version", ctypes.c_char*10),
        ("Date", ctypes.c_char*12),
        ("Select", ctypes.c_byte),
        ("Type", ctypes.c_byte),
        ("Reserved", ctypes.c_char)
    ]


class ThorlabsDCx(Camera):
    """Class for Thorlabs DCx series cameras."""

    """Initialize the camera."""
        # Load the library.
    def initialize(self, **kwargs):

        uc480_file = 'C:\\Program Files\\Thorlabs\\Scientific Imaging\\ThorCam\\uc480_64.dll'
        self.clib = windll.LoadLibrary(uc480_file)


        
        '''if 'win' in sys.platform:
            try:
                self.clib = ctypes.cdll.uc480_64
            except:
                self.clib = ctypes.cdll.uc480
        else:
            self.clib = ctypes.cdll.LoadLibrary('libueye_api.so')'''



        # Initialize the camera. The filehandle being 0 initially
        # means that the first available camera will be used. This is
        # not really the right way of doing things if there are
        # multiple cameras installed, but it's good enough for a lot
        # of cases.
        number_of_cameras = ctypes.c_int(0)
        _chk(self.clib.is_GetNumberOfCameras(byref(number_of_cameras)))
        if number_of_cameras.value < 1:
            raise RuntimeError("No camera detected!")
        self.filehandle = ctypes.c_int(0)
        _chk(self.clib.is_InitCamera(
            ctypes.pointer(self.filehandle)))

        # Resolution of camera. (height, width)
        AOI = self.get_roi()
        #print("Width, Height =%d, %d" % (AOI.s32Width, AOI.s32Height))
        self.shape = (AOI.s32Width, AOI.s32Height)
        self.props.load('thorlabs_dcx.json')

        # Allocate memory:
        # Declare variables for storing memory ID and memory start location:
        self.pid = ctypes.c_int()
        self.ppcImgMem = ctypes.c_char_p()

        # Setting monocrome 8 bit color mode
        # (otherwise we would get several identical readings per pixel!)
        _chk(self.clib.is_SetColorMode(self.filehandle, 6))

        # Allocate the right amount of memory:
        bitdepth = 8  # Camera is 8 bit.
        _chk(self.clib.is_AllocImageMem(
            self.filehandle, self.shape[0], self.shape[1], bitdepth,
            byref(self.ppcImgMem),  byref(self.pid)))

        # Tell the driver to use the newly allocated memory:
        _chk(self.clib.is_SetImageMem(
            self.filehandle, self.ppcImgMem, self.pid))

        # Enable autoclosing. This allows for safely closing the
        # camera if it is disconnected.
        _chk(self.clib.is_EnableAutoExit(self.filehandle, 1))

    def close(self):
        """Close the camera safely."""
        _chk(self.clib.is_ExitCamera(self.filehandle))

    def start(self):
        print("Starting??")

    def stop(self):
        print("Stopping??")

    def set_acquisition_mode(self, mode):
        """Set the image acquisition mode."""

    def get_display_mode(self):
        return self.clib.is_SetDisplayMode(self.filehandle, 0x8000)

    def acquire_image_data(self):
        """Code for getting image data from the camera should be
        placed here.

        """
        # Allocate memory for image:
        img_size = self.shape[0]*self.shape[1]/self.bins**2
        c_array = ctypes.c_char*int(img_size)
        c_img = c_array()

        # Take one picture: wait time is waittime * 10 ms:
        waittime = c_int(100)
        _chk(self.clib.is_FreezeVideo(self.filehandle, waittime))

        # Copy image data from the driver allocated memory to the memory that we
        # allocated.
        _chk(self.clib.is_CopyImageMem(
            self.filehandle, self.ppcImgMem, self.pid, c_img))

        # Pythonize and return.
        img_array = np.frombuffer(c_img, dtype=ctypes.c_ubyte)
        img_array.shape = (1024, 1280)  # FIXME
        return img_array

    def get_trigger_mode(self):
        """Query the current trigger mode."""

    def set_trigger_mode(self, mode):
        """Setup trigger mode."""

    def trigger(self):
        """Send a software trigger to take an image immediately."""

    def open_shutter(self):
        """Open the shutter."""
        self.shutter_open = True

    def close_shutter(self):
        """Close the shutter."""
        self.shutter_open = False

    def update_exposure_time(self, t, units='ms'):
        """Set the exposure time."""
        IS_EXPOSURE_CMD_SET_EXPOSURE = 12
        nCommand = IS_EXPOSURE_CMD_SET_EXPOSURE
        Param = c_double(t)
        SizeOfParam = 8
        _chk(self.clib.is_Exposure(
            self.filehandle, nCommand, byref(Param), SizeOfParam))

    def get_gain(self):
        """Query the current gain settings."""

    def set_gain(self, gain, **kwargs):
        """Set the camera gain."""

    def get_roi(self):
        """Define the region of interest."""
        rectAOI = IS_RECT()
        _chk(self.clib.is_AOI(self.filehandle, 2, pointer(rectAOI), 4*4))
        return rectAOI

    def save_image(self):
        size = sizeof(ImageFileParams)
        params = ImageFileParams()
        params.nQuality = 0
        params.pwchFileName = u"mypic.bmp"
        params.ppcImageMem = None
        print("size", size)
        _chk(self.clib.is_ImageFile(self.filehandle, 2, pointer(params), size))

    def get_parameters(self):
        _chk(self.clib.is_ParameterSet(self.filehandle, 4, "file.ini", None))

    def set_roi_shape(self, set_roi_shape):
        class IS_SIZE_2D(Structure):
            _fields_ = [('s32Width', c_int), ('s32Height', c_int)]
        AOI_size = IS_SIZE_2D(set_roi_shape[0], set_roi_shape[1]) #Width and Height
            
        is_AOI = self.clib.is_AOI
        is_AOI.argtypes = [c_int, c_uint, POINTER(IS_SIZE_2D), c_uint]
        i = is_AOI(self.filehandle, 5, byref(AOI_size), 8 )#5 for setting size, 3 for setting position
        is_AOI(self.filehandle, 6, byref(AOI_size), 8 )#6 for getting size, 4 for getting position
        self.roi_shape = [AOI_size.s32Width, AOI_size.s32Height]
                # Resolution of camera. (height, width)
        self.props.load('thorlabs_dcx.json')
        if i == 0:
            print("ThorCam ROI size set successfully.")
            #self.initialize_memory()
        else:
            print("Set ThorCam ROI size failed with error code "+str(i))

    def set_roi_pos(self, set_roi_pos):
        class IS_POINT_2D(Structure):
            _fields_ = [('s32X', c_int), ('s32Y', c_int)]
        AOI_pos = IS_POINT_2D(set_roi_pos[0], set_roi_pos[1]) #Width and Height
            
        is_AOI = self.clib.is_AOI
        is_AOI.argtypes = [c_int, c_uint, POINTER(IS_POINT_2D), c_uint]
        i = is_AOI(self.filehandle, 3, byref(AOI_pos), 8 )#5 for setting size, 3 for setting position
        is_AOI(self.filehandle, 4, byref(AOI_pos), 8 )#6 for getting size, 4 for getting position
        self.roi_pos = [AOI_pos.s32X, AOI_pos.s32Y]
        if i == 0:
            print("ThorCam ROI position set successfully.")
        else:
            print("Set ThorCam ROI size failed with error code "+str(i))