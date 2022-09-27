# Python Module Dependency Groups
Accepts Python modules as arguments, does a topological sort of the combined
dependency tree and then outputs groups of modules, one group per line, in the
order they should be built to satisfy dependencies.

## Rationale
This is useful if we're automatically building wheels from source [in Docker
containers][musl-wheels].

i.e. There's no point building _cffi_ as part of the _cryptography_ build when
we're building _cffi_ standalone in another container anyway. Build _cffi_
first, then it can be imported into the _cryptography_ build.

Outputting space-separated groups of modules in the order they should be built
is convenient for handling in shell scripts.

## Usage
Use the standalone script (after installing `requirements.txt`) or the Docker
image in the same way:

```
./pydepgroups.py <mods>

# .. or ..

docker run --rm moonbuggy2000/python-depenency-groups <mods>
```
Where `<mods>` is a space separated string of module names.

The output will use module names from the PyPi API, which may result in the
case changing from the input, as with _PyNaCl_ in this example:
```
$ ./pydepgroups.py cryptography paramiko pynacl
bcrypt pycparser PyNaCl six
cffi
cryptography
paramiko
```

Arguments may include a version number, in the form `<module>-<version>`. If no
version number is provided the dependencies for the latest version will be used.
Modules specified with a version number will be returned with the version number
intact.

For example (note that this older _paramiko_ version doesn't depend on _six_):
```
$ ./pydepgroups.py cryptography paramiko-2.7.2 pynacl
bcrypt pycparser PyNaCl
cffi
cryptography
paramiko-2.7.2
```

A practical application in a shell script:
```
#! /bin/bash

modules="cryptography paramiko PyNaCl"

build_wheels () {
  # called four times, with arguments:
  #   1st: bcrypt pycparser PyNaCl six
  #   2nd: cffi
  #   3rd: cryptography
  #   4th: paramiko

  for wheel in "$@"; do
    # .. import dependencies ..
    # .. build individual wheel ..
  done
}

while read -r line; do
  build_wheels $line
done < <(./pydepgroups.py $modules)
```

## Links
GitHub: <https://github.com/moonbuggy/python-dependency-groups>

Docker Hub: <https://hub.docker.com/r/moonbuggy2000/python-dependency-groups>

Related:
*   <https://github.com/moonbuggy/docker-python-musl-wheels>

[musl-wheels]: https://github.com/moonbuggy/docker-python-musl-wheels
