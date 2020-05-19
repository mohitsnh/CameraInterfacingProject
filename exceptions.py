"""Error and warning types for qCamera exceptions."""


class CameraError(Exception):
    """Generic camera errors."""


class ConnectionError(CameraError):
    """Camera connection errors."""


class AndorError(CameraError):
    """Andor-specific errors."""


class RemoteCameraError(CameraError):
    """RPC camera errors."""


class SensicamError(CameraError):
    """Sensicam errors."""


class ThorlabsDCxError(CameraError):
    """Thorlabs DCx series errors."""


class OpenCVError(CameraError):
    """Errors for OpenCV cameras."""


class CameraPropertiesError(Exception):
    """Error type for exceptions raised by CameraProperties
    objects.

    """
