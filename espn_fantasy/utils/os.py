import platform


def get_os() -> str:
    system = platform.system().lower()  # darwin, linux, windows
    machine = platform.machine().lower()  # arm64, x86_64, etc.

    # Normalize platform names
    if system == "darwin":
        system = "macos"
    elif system == "windows":
        machine = "x64"  # oracle uses x64 for Windows ZIPs

    return f"{system}-{machine}"  # ex: macos-arm64, linux-x86_64
