"""Check the wheel matrix: one abi3 wheel per architecture, plus the sdist.

The extension uses the limited API, so the expected wheels are
`cp37-abi3-win_amd64` and `cp37-abi3-win32` -- NOT one per interpreter. A
per-version tag here would mean `--py-limited-api` was not passed to
`bdist_wheel`, and a 3.7 interpreter would then have nothing to install.
"""

import glob
import os
import sys
import zipfile

dist = sys.argv[1] if len(sys.argv) > 1 else "dist"
expected_archs = ("win_amd64", "win32")
expected_tag = "cp37-abi3"

problems = []
seen = set()

for path in sorted(glob.glob(os.path.join(dist, "*.whl"))):
    name = os.path.basename(path)
    with zipfile.ZipFile(path) as wheel:
        meta = [n for n in wheel.namelist() if n.endswith(".dist-info/WHEEL")]
        tag = ""
        if meta:
            for line in wheel.read(meta[0]).decode().splitlines():
                if line.startswith("Tag:"):
                    tag = line.split(":", 1)[1].strip()
        extensions = [n for n in wheel.namelist() if n.endswith((".pyd", ".so"))]
        # The stub and the py.typed marker have to travel too: a wheel without
        # them type-checks as an untyped module.
        has_stub = any(n.endswith("__init__.pyi") for n in wheel.namelist())

    arch = name.rsplit("-", 1)[-1].replace(".whl", "")
    ok = (bool(extensions) and tag.startswith(expected_tag) and has_stub
          and arch in expected_archs)
    if not ok:
        problems.append(name)
    seen.add(arch)
    print("%-52s tag=%-22s ext=%d stub=%s  %s" % (
        name, tag, len(extensions), has_stub,
        extensions[0] if extensions else "NO EXTENSION"))

print()
missing = [arch for arch in expected_archs if arch not in seen]
sdist = glob.glob(os.path.join(dist, "*.tar.gz"))
print("wheels:", len(glob.glob(os.path.join(dist, "*.whl"))), "expected 2")
print("sdist :", os.path.basename(sdist[0]) if sdist else "MISSING")
print("missing:", missing if missing else "none")
print("problems:", problems if problems else "none")
sys.exit(1 if (missing or problems or not sdist) else 0)
