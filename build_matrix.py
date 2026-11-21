"""Build the tree-sitter-metal wheels: one abi3 wheel per architecture, plus the sdist.

Because the extension is built against the **limited API** (`py_limited_api`,
`Py_LIMITED_API=0x03070000`), one wheel per architecture serves every CPython
from 3.7 up -- `cp37-abi3-win_amd64`, not one wheel per interpreter. That is the
same shape `tree-sitter-opencl` ships, and it is what makes a 3.7 interpreter
load the wheel built by a 3.14 one.

The tag no longer has to be passed on the command line: `setup.py` carries
`options={"bdist_wheel": {"py_limited_api": "cp37"}}`, so any build front end --
this script, `python -m build`, `pip wheel`, cibuildwheel -- produces abi3
without being told. That is deliberate: a forgotten flag was exactly how
`tree-sitter-opencl` shipped eighteen per-version wheels while its extension was
already limited-API.

The build interpreter only has to be new enough to run setuptools and to provide
a stable ABI; anything 3.7+ works. The sdist is built once, from the 64-bit
interpreter, so PyPI has sources alongside the binaries.
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# One entry per architecture. A 32-bit interpreter produces the win32 abi3 wheel.
INTERPRETERS = [
    (r"D:\Python\37\python.exe", True),        # also builds the sdist
    (r"D:\Python\37-32\python.exe", False),
]


def main() -> int:
    dist = os.path.join(ROOT, "dist")
    shutil.rmtree(dist, ignore_errors=True)
    shutil.rmtree(os.path.join(ROOT, "build"), ignore_errors=True)
    os.makedirs(dist, exist_ok=True)

    failures = []
    for python, with_sdist in INTERPRETERS:
        if not os.path.exists(python):
            failures.append((python, "missing interpreter"))
            continue
        commands = ["bdist_wheel", "--dist-dir", dist]
        if with_sdist:
            commands = ["sdist", "--dist-dir", dist] + commands
        # A stale build/ directory would leak objects compiled for the previous
        # architecture into this wheel, so it is removed before every build.
        shutil.rmtree(os.path.join(ROOT, "build"), ignore_errors=True)
        result = subprocess.run(
            [python, "setup.py"] + commands,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if result.returncode != 0:
            tail = result.stdout.decode("utf-8", "replace").strip().splitlines()[-6:]
            failures.append((python, "\n".join(tail)))
            print("FAILED:", python)
        else:
            print("ok:", python)

    artifacts = sorted(f for f in os.listdir(dist)
                       if f.endswith((".whl", ".tar.gz")))
    print("\n=== %d artifact(s) ===" % len(artifacts))
    for name in artifacts:
        print(name)

    # Each architecture must have produced exactly one abi3 wheel. A wheel named
    # cpXXX-cpXXX means the limited-API option stopped taking effect.
    wheels = [f for f in artifacts if f.endswith(".whl")]
    bad = [f for f in wheels if "-abi3-" not in f]
    if bad:
        failures.append(("dist/", "not abi3: %s" % ", ".join(bad)))
    if len(wheels) != len(INTERPRETERS):
        failures.append(("dist/", "%d wheels for %d architectures" % (len(wheels), len(INTERPRETERS))))

    if failures:
        print("\n=== failures ===")
        for python, message in failures:
            print(python, "->", message)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
