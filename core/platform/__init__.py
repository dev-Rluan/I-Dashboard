import platform as _platform

from .base import AbstractPlatform


def get_platform() -> AbstractPlatform:
    os_name = _platform.system()
    if os_name == "Linux":
        from .linux import LinuxPlatform
        return LinuxPlatform()
    if os_name == "Windows":
        from .windows import WindowsPlatform
        return WindowsPlatform()
    if os_name == "Darwin":
        from .macos import MacOSPlatform
        return MacOSPlatform()
    raise RuntimeError(f"Unsupported OS: {os_name}")


__all__ = ["get_platform", "AbstractPlatform"]
