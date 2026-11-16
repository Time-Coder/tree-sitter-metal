"""Upload every built artifact to PyPI with twine.

The glob has to be expanded here rather than left in the file name: a shell
expands `dist/*.whl`, but `twine` invoked through `subprocess` receives the
pattern literally on Windows, which then fails with "no such file". The sdist is
listed too -- it is what a user on a platform without a wheel installs from.
"""

import glob
import subprocess
import sys

artifacts = sorted(glob.glob("dist/*.whl") + glob.glob("dist/*.tar.gz"))
if not artifacts:
    print("nothing in dist/ to upload")
    raise SystemExit(1)

print("uploading %d artifact(s):" % len(artifacts))
for path in artifacts:
    print("  ", path)

subprocess.check_call([sys.executable, "-m", "twine", "upload"] + artifacts)
