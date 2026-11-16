"""Build the wheels for every interpreter this machine has, and repair them on Linux.

Thin wrapper around the platform's interpreters: it discovers them, builds the
sdist once and a wheel per architecture, and on Linux runs `auditwheel repair`
so the wheel is manylinux-tagged instead of depending on the build host's libc.

The Windows/macOS side needs no repair -- a win_amd64 or macosx wheel is already
self-contained -- which is why `build_matrix.py` is the plain, explicit version
of this and this script is the convenience one.
"""

import glob
import os
import platform
import subprocess

# The interpreters, by directory. `-32` is the 32-bit build.
VERSIONS = ["37", "38", "39", "310", "311", "312", "313", "314", "315"]
SUFFIXES = ["", "-32"]


def interpreters():
    """Every interpreter directory this machine actually has."""
    found = []
    for version in VERSIONS:
        for suffix in SUFFIXES:
            python = os.path.join("D:\\Python", version + suffix, "python.exe")
            if os.path.exists(python):
                found.append(python)
    return found


def build(python: str, with_sdist: bool) -> None:
    commands = ["setup.py", "bdist_wheel", "--py-limited-api", "cp37"]
    if with_sdist:
        commands.insert(1, "sdist")
    try:
        subprocess.check_call([python] + commands)
    except subprocess.CalledProcessError:
        # A fresh interpreter may lack the build tools; install and retry once.
        subprocess.check_call([python, "-m", "pip", "install", "--upgrade",
                               "wheel", "setuptools"])
        subprocess.check_call([python] + commands)


def main() -> int:
    pythons = interpreters()
    if not pythons:
        print("no interpreters found")
        return 1

    # The 64-bit, newest interpreter builds the sdist as well.
    ordered = sorted(pythons, key=lambda path: ("-32" in path, path))
    for index, python in enumerate(ordered):
        print("building with", python)
        build(python, with_sdist=(index == 0))

    if platform.system() == "Linux":
        machine = platform.machine()
        for wheel in glob.glob("dist/tree_sitter_metal-*-linux_%s.whl" % machine):
            try:
                subprocess.check_call([ordered[0], "-m", "auditwheel", "repair",
                                       wheel, "--plat=manylinux_2_5_%s" % machine,
                                       "-w", "dist"])
            except subprocess.CalledProcessError:
                subprocess.check_call([ordered[0], "-m", "pip", "install", "auditwheel"])
                subprocess.check_call([ordered[0], "-m", "auditwheel", "repair", wheel,
                                       "--plat=manylinux_2_5_%s" % machine,
                                       "-w", "dist"])
            os.remove(wheel)

    artifacts = sorted(f for f in os.listdir("dist")
                       if f.endswith((".whl", ".tar.gz")))
    print("\n=== %d artifact(s) ===" % len(artifacts))
    for name in artifacts:
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
