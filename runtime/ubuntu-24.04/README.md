# USaD Ubuntu 24.04 Multi-language Developer Image

This image is a Linux programming environment for learning and web development,
not a complete web terminal service. It does not provide authentication,
session management, workspace authorization, WebSocket transport, persistent
storage management, or a Docker control API.

The base is `ubuntu:24.04`. User-space package versions are resolved from
Ubuntu 24.04 repositories at build time (not pinned to package revision), so
the precise patch versions can change with Ubuntu updates. Node.js is pinned
to **24.21.0 LTS** from the official Node.js distribution and verified against
its published SHA-256 checksum; npm is bundled with that Node.js release.
OpenJDK 21 is installed from Ubuntu's headless package.

The expected Ubuntu 24.04 package series are Python 3.12, PHP 8.3, Go 1.22,
Rust 1.75, and Ruby 3.2; Composer, database clients, and utilities use the
Ubuntu 24.04 repository versions. Exact installed versions are reported by the
smoke-test commands below. `ubuntu:24.04` is a versioned tag, not a
digest-pinned immutable base.

`vim-tiny` is used to reduce image size and is exposed as `vim`; Ubuntu's
`fd-find` package is exposed as both `fdfind` and `fd`. Python remains managed by
Ubuntu packages: install project packages inside a virtual environment created
with `python3 -m venv`, rather than changing the system Python. The image has
no desktop, systemd, SSH server, credentials, or private keys. Interactive
programs run as unprivileged user `developer` (UID 10001); `/workspace` is the
working directory.

## Build locally

Run from PowerShell at the repository root. This uses a new tag and will not
overwrite the existing single-language image:

```powershell
docker build --pull --build-arg NODE_VERSION=24.21.0 -t usad-dev:24.04-multilang-node24.21.0-java21 .\runtime\ubuntu-24.04
```

The build downloads packages from Ubuntu's configured package repositories and
Node.js from `nodejs.org`; network access is required during the build. The
Dockerfile supports `amd64` and `arm64`.

## Offline smoke tests

Print the effective user and versions for the requested languages and main
tools. The test container has networking disabled:

```powershell
docker run --rm --network none --entrypoint /bin/bash usad-dev:24.04-multilang-node24.21.0-java21 -lc 'set -eu; id; test "$(id -u)" = 10001; test "$PWD" = /workspace; python3 --version; git --version; gcc --version | head -n 1; node --version; npm --version; java -version 2>&1 | head -n 1; php --version | head -n 1; composer --version; sqlite3 --version; mysql --version; psql --version; go version; rustc --version; cargo --version; ruby --version; gem --version; gdb --version | head -n 1; jq --version; tree --version | head -n 1; rg --version | head -n 1; fd --version; tmux -V; xxd -h 2>&1 | head -n 1'
```

Check PHP extensions and that Python venv creation does not replace the system
interpreter:

```powershell
docker run --rm --network none --entrypoint /bin/bash usad-dev:24.04-multilang-node24.21.0-java21 -lc 'set -eu; php -m; base_python="$(readlink -f "$(command -v python3)")"; temp_dir="$(mktemp -d)"; python3 -m venv "$temp_dir/venv"; "$temp_dir/venv/bin/python" --version; test "$(readlink -f "$(command -v python3)")" = "$base_python"; rm -rf "$temp_dir"'
```

Check Node.js can parse JavaScript and PHP CLI executes code without network:

```powershell
docker run --rm --network none --entrypoint /bin/bash usad-dev:24.04-multilang-node24.21.0-java21 -lc 'set -eu; printf "console.log(\"USaD JS smoke test\");\n" >/tmp/usad-smoke.js; node --check /tmp/usad-smoke.js; node /tmp/usad-smoke.js; php -r "echo \"USaD PHP smoke test\\n\";"'
```

HTML and CSS editing is supported using the installed text editors; this image
does not include dedicated HTML/CSS validators or a browser/desktop UI.

## Start a restricted local test container

First create a local workspace directory from the repository root:

```powershell
New-Item -ItemType Directory -Force .\workspace
$workspacePath = (Resolve-Path .\workspace).Path
docker run --rm -it --network none --cpus=0.5 --memory=768m --pids-limit=128 --cap-drop=ALL --security-opt=no-new-privileges --mount "type=bind,source=$workspacePath,target=/workspace" usad-dev:24.04-multilang-node24.21.0-java21
```

This starts interactive Bash with networking disabled, bounded local resources,
all Linux capabilities dropped, and `no-new-privileges`. The workspace mount is
the only host path explicitly mounted by this example and persists when the
`--rm` container exits. Do not add `--privileged`, mount
`/var/run/docker.sock`, pass arbitrary host paths, or enable networking
casually. These settings are a local smoke-test configuration, not proof of
multi-user isolation or production readiness.

## Tool selection and version commands

| Tools | Source / expected version series | Verify with |
|---|---|---|
| Ubuntu | `ubuntu:24.04` | `cat /etc/os-release` |
| Bash, coreutils, findutils, grep, sed, gawk, less | Ubuntu 24.04 packages | `bash --version`; `dpkg-query -W coreutils findutils grep sed gawk less` |
| nano, vim (`vim-tiny`), procps, iproute2, iputils-ping | Ubuntu 24.04 packages | `nano --version`; `vim --version`; `ps --version`; `ip -Version`; `ping -V` |
| ca-certificates, curl, wget, tar, gzip, unzip, zip, file, xxd, tree, tmux | Ubuntu 24.04 packages | `dpkg-query -W ca-certificates curl wget tar gzip unzip zip file xxd tree tmux` |
| Python, pip, venv | Ubuntu 24.04 packages; Python 3.12 series | `python3 --version`; `python3 -m pip --version`; `python3 -m venv /tmp/test-venv` |
| Git | Ubuntu 24.04 package | `git --version` |
| GCC, G++, Make, GDB | Ubuntu 24.04 packages; Noble GCC 13 series | `gcc --version`; `g++ --version`; `make --version`; `gdb --version` |
| Node.js, npm | Node.js 24.21.0 LTS official distribution; npm bundled | `node --version`; `npm --version` |
| OpenJDK | Ubuntu 24.04 headless package; Java 21 | `java -version`; `javac -version` |
| PHP CLI and common extensions (curl, GD, intl, mbstring, MySQL, PostgreSQL, SQLite, XML, zip, bcmath) | Ubuntu 24.04 packages; PHP 8.3 series | `php --version`; `php -m` |
| Composer | Ubuntu 24.04 package | `composer --version` |
| SQLite, MySQL-compatible client, PostgreSQL client | Ubuntu 24.04 packages | `sqlite3 --version`; `mysql --version`; `psql --version` |
| Go | Ubuntu 24.04 `golang-go`; Go 1.22 series | `go version` |
| Rust | Ubuntu 24.04 `rustc`/`cargo`; Rust 1.75 series | `rustc --version`; `cargo --version` |
| Ruby and RubyGems | Ubuntu 24.04 packages; Ruby 3.2 series | `ruby --version`; `gem --version` |
| jq, ripgrep, fd-find | Ubuntu 24.04 packages; `fd` links to `fdfind` | `jq --version`; `rg --version`; `fd --version` |

Ubuntu security updates may advance package patch versions while retaining the
release series. Capture the exact output of the smoke tests for a particular
build; no claim of immutable package revisions is made. The image has not been
built or run as part of this change unless local Docker build/test results are
reported separately.
