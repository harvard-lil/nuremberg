#!/bin/bash
set -euo pipefail

# Next, install Debian/Ubuntu packages specified on the command-line. We
# can't use Python because it may not be installed at this point!# CHANGEME:
# If you want to add PPAs and the like, this is a good place to add these.

# Disable interactive use by the Debian installer:
export DEBIAN_FRONTEND=noninteractive

# Update package cache and upgrade all packages to ensure we have latest
# packages.
apt-get update
apt-get upgrade --yes

# Use --no-install-recommends so we only install packages we actually need.
apt-get install --yes --no-install-recommends "$@"

# Clear the various apt caches once the packages are installed, just to save
# a little disk space. We do this in same Dockerfile line so that there are
# no intermediate layes where the cached files will still exist.
apt-get clean
rm -rf /var/lib/apt/lists/*
