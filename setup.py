from os.path import isdir, join
from platform import system

from setuptools import Extension, find_packages, setup
from distutils.command.build import build

# `wheel` is imported by `bdist_wheel`, which is a build command -- but this module
# is also imported for `sdist`, `egg_info` and a plain `pip install` from a source
# tree, and those run in environments that have no `wheel` installed. Importing it
# at module scope made every one of them fail with "No module named 'wheel'",
# which is exactly what a bare CPython 3.7 venv does.
try:
    from wheel.bdist_wheel import bdist_wheel  # noqa: F401  (registers the command)
except ImportError:  # pragma: no cover - a build without wheel cannot bdist_wheel
    bdist_wheel = None


class Build(build):
    def run(self):
        if isdir("queries"):
            dest = join(self.build_lib, "tree_sitter_metal", "queries")
            self.copy_tree("queries", dest)
        super().run()


setup(
    name="tree-sitter-metal",
    version="0.1.0",
    description="Metal Shading Language grammar for tree-sitter",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Time-Coder/tree-sitter-metal",
    project_urls={
        "Source": "https://github.com/Time-Coder/tree-sitter-metal",
        "Upstream grammar": "https://github.com/save-buffer/tree-sitter-metal",
        "Parser": "https://github.com/Time-Coder/PyGPGPU",
    },
    author="Binghui Wang",
    license="MIT",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: C",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Compilers",
        "Topic :: Text Processing :: Linguistic",
        "Typing :: Typed",
    ],
    keywords="tree-sitter metal msl grammar parser shader apple",
    packages=find_packages("bindings/python"),
    package_dir={"": "bindings/python"},
    package_data={
        "tree_sitter_metal": ["*.pyi", "py.typed"],
        "tree_sitter_metal.queries": ["*.scm"],
    },
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
                ["-std=c11"] if system() != 'Windows' else []
            ),
            define_macros=[
                ("Py_LIMITED_API", "0x03070000"),
                ("PY_SSIZE_T_CLEAN", None)
            ],
            include_dirs=["src"],
            py_limited_api=True,
        )
    ],
    cmdclass={
        "build": Build
    },
    zip_safe=False
)
