"""Install the built abi3 wheels into real interpreters and parse MSL with them.

Because the extension uses the limited API, one wheel per architecture serves
every CPython from 3.7 up. So the question this answers is not "did each
interpreter get a wheel" but "does the *same* wheel load and parse on all of
them" -- which is the property the ABI 13 + abi3 choice exists to provide.

Each interpreter is checked with the tree-sitter version that has wheels for it:
0.20.4 on the 3.7 line, whatever is current on the rest.
"""

import glob
import os
import subprocess
import sys

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

# (interpreter version, architecture suffix). The suffix is appended to the
# interpreter directory name: `D:\Python\37-32` is the 32-bit build.
INTERPRETERS = [
    ("37", ""), ("37", "-32"),
    ("38", ""), ("38", "-32"),
    ("39", ""), ("39", "-32"),
    ("310", ""), ("310", "-32"),
    ("311", ""), ("311", "-32"),
    ("312", ""), ("312", "-32"),
    ("313", ""), ("313", "-32"),
    ("314", ""), ("314", "-32"),
    ("315", ""), ("315", "-32"),
]

CHECK = (
    "import tree_sitter as ts, tree_sitter_metal as m\n"
    "lang = m.language()\n"
    "# The Parser API moved: 0.20.x takes the language in the constructor,\n"
    "# 0.21+ has set_language. Both have to be exercised, because a wheel that\n"
    "# only works on one line is exactly what this script is here to catch.\n"
    "if hasattr(ts.Parser, 'set_language'):\n"
    "    p = ts.Parser(); p.set_language(lang)\n"
    "else:\n"
    "    p = ts.Parser(lang)\n"
    "plain = p.parse(b'kernel void k(device float* a) { a[0] = 1.0f; }')\n"
    "atom = p.parse(b'kernel void k(device uint* x) {"
    " atomic_fetch_add_explicit((device atomic_uint*)&x[0], 1,"
    " memory_order_relaxed); }')\n"
    "assert not plain.root_node.has_error, 'plain kernel failed to parse'\n"
    "assert not atom.root_node.has_error, 'atomic cast failed to parse'\n"
    "print('ok:', ts.__name__, 'plain + atomic parse clean')\n"
)


def wheel_for(arch: str):
    """The one abi3 wheel built for this architecture."""
    if arch == "win_amd64":
        pattern = "tree_sitter_metal-*-cp37-abi3-win_amd64.whl"
    else:
        pattern = "tree_sitter_metal-*-cp37-abi3-win32.whl"
    matches = sorted(glob.glob(os.path.join(DIST, pattern)))
    return matches[0] if matches else None


def main() -> int:
    failures = []
    checked = 0
    for version, suffix in INTERPRETERS:
        python = r"D:\Python\%s%s\python.exe" % (version, suffix)
        if not os.path.exists(python):
            print("%-34s skipped (not installed)" % python)
            continue
        arch = "win_amd64" if not suffix else "win32"
        wheel = wheel_for(arch)
        if wheel is None:
            failures.append((python, "no abi3 wheel for " + arch))
            continue

        # tree-sitter itself is a per-interpreter wheel; install whatever that
        # interpreter can get, then this package without touching it.
        subprocess.run(
            [python, "-m", "pip", "install", "--quiet", "--no-warn-script-location",
             "--upgrade", "tree-sitter"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        install = subprocess.run(
            [python, "-m", "pip", "install", "--quiet", "--no-warn-script-location",
             "--force-reinstall", "--no-deps", wheel],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        if install.returncode != 0:
            failures.append((python, install.stdout.decode("utf-8", "replace")[-300:]))
            print("%-34s FAIL install" % python)
            continue

        proc = subprocess.run([python, "-c", CHECK],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = proc.stdout.decode("utf-8", "replace").strip().splitlines()
        if proc.returncode != 0:
            failures.append((python, "\n".join(output[-3:])))
            print("%-34s FAIL %s" % (python, output[-1] if output else ""))
        else:
            checked += 1
            print("%-34s %s" % (python, output[-1] if output else "ok"))

    print("\nchecked %d interpreter(s)" % checked)
    if failures:
        print("\n=== failures ===")
        for python, message in failures:
            print(python, "->", message)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
