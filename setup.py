"""Build the tree-sitter-metal extension.

Only the Extension lives here. Every piece of *metadata* -- name, version,
readme, dependencies, classifiers, package discovery, package data -- is in
``pyproject.toml``, which is the single source for all of it.

Why the Extension cannot move into pyproject.toml as well: the declarative
``[[tool.setuptools.ext-modules]]`` table arrived in setuptools 74, and
setuptools 68 is the last release that installs on Python 3.7 -- an interpreter
this package still supports (tree-sitter 0.20.x is the last line with 3.7
wheels, and the grammar is built at ABI 13 for exactly that reason). Declaring
the extension in the toml would either drop 3.7 or make every 3.7 build fail
with "``tool.setuptools`` must not contain {'ext-modules'}".

The parser needs no queries copy step: this grammar ships no ``queries/*.scm``,
so ``package-data`` has nothing to add and the build stays the plain one.
"""

from os import name as os_name
from os.path import isdir, join

from setuptools import Extension, setup
from setuptools.command.build import build

# `wheel` backs only bdist_wheel. This module is also imported for sdist,
# egg_info and a plain source install, none of which a bare venv can satisfy.
try:
    from wheel.bdist_wheel import bdist_wheel  # noqa: F401  (registers the command)
except ImportError:  # pragma: no cover - a build without wheel cannot bdist_wheel
    bdist_wheel = None


class Build(build):
    """Copy ``queries/`` alongside the package when the grammar has any.

    The directory sits at the repository root, outside ``bindings/python``, so
    package-data cannot find it -- its source path is not inside the package
    directory. The guard keeps this a no-op for the grammar as it stands today.
    """

    def run(self):
        if isdir("queries"):
            destination = join(self.build_lib, "tree_sitter_metal", "queries")
            self.copy_tree("queries", destination)
        super().run()


setup(
    ext_package="tree_sitter_metal",
    ext_modules=[
        Extension(
            name="_binding",
            sources=[
                "bindings/python/tree_sitter_metal/binding.c",
                "src/parser.c",
                "src/scanner.c",
            ],
            extra_compile_args=(
                # `/std:c11` for MSVC, which rejects the C11 syntax the generated
                # parser uses without it; `-std=c11` plus hidden symbols elsewhere.
                ["/std:c11", "/utf-8"] if os_name == "nt" else ["-std=c11", "-fvisibility=hidden"]
            ),
            define_macros=[
                # The limited API floor is 3.7 and the tag is abi3, so one wheel
                # serves 3.7 through 3.15. `binding.c` uses only PyModuleDef,
                # PyModuleDef_Init and PyCapsule_New, all of which are stable ABI.
                ("Py_LIMITED_API", "0x03070000"),
                ("PY_SSIZE_T_CLEAN", None),
                # TREE_SITTER_HIDE_SYMBOLS is deliberately NOT defined here, even
                # though it would keep the grammar's symbols out of the dynamic
                # symbol table. This grammar's `src/parser.c` honours it by
                # declaring `tree_sitter_metal` static (line 549391 in the
                # generated file), and `__init__.py` loads exactly that symbol
                # through ctypes on tree-sitter 0.20.x-0.22.x -- the legacy path
                # that has no capsule API. Defining the macro made every 3.7 and
                # 3.8 interpreter fail with "function 'tree_sitter_metal' not
                # found". tree-sitter-opencl and tree-sitter-cuda37 do not have
                # this conflict because their generated parsers ignore the macro.
            ],
            include_dirs=["src"],
            py_limited_api=True,
        )
    ],
    # The abi3 *tag* comes from this option, not from `py_limited_api` alone:
    # `py_limited_api=True` only changes how the extension is built, and a plain
    # `bdist_wheel` would still tag the wheel cp37-cp37m. Set here so every build
    # front end -- `build`, `pip wheel`, cibuildwheel -- produces abi3 without
    # being told to, which is what makes the wheel count one per platform.
    options={"bdist_wheel": {"py_limited_api": "cp37"}},
    cmdclass={"build": Build},
)
