class InternetDevice:
    """Base class for all internet-connected devices."""

    def __init__(self, ip, device_name=""):
        self.device_name = device_name
        self.ip = ip # ip address

    def __str__(self):
        return f"{self.device_name} ({self.ip})"
