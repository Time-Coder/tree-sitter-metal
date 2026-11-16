# tree-sitter-metal

A [tree-sitter](https://tree-sitter.github.io/) grammar for **Metal Shading
Language** (MSL), packaged for Python -- with an extension for the address-space
cast form MSL's atomics need.

This is the grammar [PyGPGPU](https://github.com/Time-Coder/PyGPGPU) reads its
Metal sources with. It exists as its own distribution because no MSL grammar was
installable from PyPI: the `tree-sitter-metal` names found on GitHub are Neovim
highlighting plugins with no grammar at all.

## Install

```sh
pip install tree-sitter-metal
```

```python
import tree_sitter, tree_sitter_metal

parser = tree_sitter.Parser()
parser.set_language(tree_sitter_metal.language())   # tree-sitter 0.21+
# legacy (0.20.x): parser.set_language(tree_sitter_metal.language())
tree = parser.parse(b"kernel void k(device float* a) { a[0] = 1.0f; }")
print(tree.root_node.has_error)   # False
```

`language()` answers a native `tree_sitter.Language` on both the legacy 0.20.x
line and 0.21+, so one wheel serves every supported interpreter -- see
[ABI 13](#abi-13-and-why) below.

## Origin

Built from [`save-buffer/tree-sitter-metal`](https://github.com/save-buffer/tree-sitter-metal),
a tree-sitter-cpp descendant that already handles MSL's scalar and vector types,
address-space words and `[[attributes]]`. Two changes are carried on top:

1. **An address space may qualify a cast's type** -- `(device atomic_uint*)&x[0]`.
   The base grammar accepted those words only in a declaration position, so MSL's
   atomics (which are all cast-and-update) parsed as `ERROR` nodes. The extension
   adds a `type_descriptor` alternative taking a `storage_class_specifier` head,
   wrapped in `prec.right` to settle the shift/reduce conflict.
2. The grammar is generated at **ABI 13** rather than the current 15.

The generated `src/parser.c` is committed, so building the wheel needs a C
compiler and nothing else.

## Building from source

The wheel is a plain setuptools extension:

```sh
pip install -e .
```

To regenerate `src/parser.c` after editing `grammar.js` you need the tree-sitter
CLI and the two grammars this one descends from:

```sh
git clone https://github.com/tree-sitter/tree-sitter-cpp node_modules/tree-sitter-cpp
git clone https://github.com/tree-sitter/tree-sitter-c node_modules/tree-sitter-c
tree-sitter generate --abi 13
```

**The CLI version matters.** `--abi 13` needs the 0.22.6 CLI: 0.27 refuses
anything below 14, and the CLI bundled with 0.20.x crashes under Node 24 while
loading `grammar.js`. Generate with 0.22.6 and a Node new enough to load a modern
`grammar.js` but old enough for that CLI -- Node 18 works:

```sh
tree-sitter-0.22.6 generate --abi 13 --js-runtime /path/to/node18/bin/node
```

### ABI 13, and why

[PyGPGPU](https://github.com/Time-Coder/PyGPGPU) supports Python 3.7, and the
last tree-sitter line with CPython 3.7 wheels is 0.20.4 -- which accepts
language ABI 13. A parser generated at 13 also loads on 0.21+, so **one wheel
serves CPython 3.7 through the current release**:

| interpreter | tree-sitter | loads |
| --- | --- | --- |
| CPython 3.7.9 | 0.20.4 | yes |
| CPython 3.14 | 0.25.2 | yes |

A parser generated at ABI 14 or 15 would be invisible to every 3.7 interpreter.

## Building the wheel matrix

`build_matrix.py` builds a wheel per interpreter and one sdist, and
`verify_dist.py` checks what came out:

```sh
python build_matrix.py     # edit INTERPRETERS at the top first
python verify_dist.py dist
python test_wheels.py dist # imports each wheel in its own interpreter
```

`upload.py` uploads the wheels with `twine`.

## License

MIT. See [LICENSE](LICENSE). The grammar descends from
[tree-sitter-cpp](https://github.com/tree-sitter/tree-sitter-cpp) and
[tree-sitter-c](https://github.com/tree-sitter/tree-sitter-c), both MIT.
