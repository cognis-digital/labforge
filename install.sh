#!/usr/bin/env sh
# Comprehensive installer for cognis-digital/labforge (Linux / macOS).
# pipx -> uv -> pip (git+https) -> source. Not on PyPI; installs from GitHub.
set -eu
REPO="labforge"
URL="git+https://github.com/cognis-digital/labforge.git"
GITURL="https://github.com/cognis-digital/labforge.git"
say() { printf '\033[1;35m[%s]\033[0m %s\n' "$REPO" "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }
if ! have python3 && ! have python; then say "Python 3.9+ required but not found."; exit 1; fi
if have pipx; then say "pipx install..."; pipx install "$URL" && { say "Done. Run: labforge --help"; exit 0; }; fi
if have uv; then say "uv install..."; uv tool install "$URL" && { say "Done. Run: labforge --help"; exit 0; }; fi
if have pip3 || have pip; then PIP="$(command -v pip3 || command -v pip)"; say "pip install..."; "$PIP" install --user "$URL" && { say "Done. Run: labforge --help"; exit 0; }; fi
say "Falling back to a source clone."
TMP="$(mktemp -d)"; git clone --depth 1 "$GITURL" "$TMP/$REPO"
say "Cloned to $TMP/$REPO — run: cd $TMP/$REPO && python3 -m pip install ."
