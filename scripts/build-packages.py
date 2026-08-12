#!/usr/bin/env python3
"""Build architecture-neutral DEB and IPK packages without host packaging tools."""

from __future__ import print_function

import argparse
import gzip
import io
import os
import re
import tarfile


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTROL_DIR = os.path.join(ROOT, "packaging", "DEBIAN")
ROOTFS_DIR = os.path.join(ROOT, "rootfs")


def read_control():
    path = os.path.join(CONTROL_DIR, "control")
    with io.open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    fields = {}
    for line in text.splitlines():
        if line and not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            fields[key] = value.strip()
    required = {"Package", "Version", "Architecture"}
    missing = sorted(required.difference(fields))
    if missing:
        raise ValueError("Missing control fields: %s" % ", ".join(missing))
    if fields["Architecture"] != "all":
        raise ValueError("Architecture-neutral release must use Architecture: all")
    config_path = os.path.join(
        ROOTFS_DIR, "usr", "lib", "enigma2", "python", "Plugins", "Extensions", "e2EPG", "config.py")
    with io.open(config_path, "r", encoding="utf-8") as handle:
        match = re.search(r'^PLUGIN_VERSION\s*=\s*["\']([^"\']+)["\']', handle.read(), re.MULTILINE)
    if not match or match.group(1) != fields["Version"]:
        raise ValueError("PLUGIN_VERSION must match the package Version")
    return fields


def validate_architecture_neutral_payload():
    for current, directories, filenames in os.walk(ROOTFS_DIR):
        directories[:] = [name for name in directories if name != "__pycache__"]
        for filename in filenames:
            path = os.path.join(current, filename)
            if filename.lower().endswith((".so", ".ko", ".a", ".o")):
                raise ValueError("Native object is not allowed in an all package: %s" % path)
            with open(path, "rb") as handle:
                magic = handle.read(4)
            if magic == b"\x7fELF" or magic[:2] == b"MZ":
                raise ValueError("Native executable is not allowed in an all package: %s" % path)


def clean_name(name):
    return name.replace(os.sep, "/")


def tar_mode(path, is_dir=False, maintainer_script=False):
    if is_dir or maintainer_script:
        return 0o755
    return 0o644


def add_tree(archive, source, control=False):
    for current, directories, filenames in os.walk(source):
        directories[:] = sorted(name for name in directories if name != "__pycache__")
        filenames = sorted(name for name in filenames if not name.endswith((".pyc", ".pyo")))
        relative_dir = os.path.relpath(current, source)
        if relative_dir != ".":
            info = tarfile.TarInfo("./" + clean_name(relative_dir))
            info.type = tarfile.DIRTYPE
            info.mode = tar_mode(current, is_dir=True)
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            archive.addfile(info)
        for filename in filenames:
            path = os.path.join(current, filename)
            relative = filename if relative_dir == "." else os.path.join(relative_dir, filename)
            info = archive.gettarinfo(path, arcname="./" + clean_name(relative))
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            info.mode = tar_mode(path, maintainer_script=control and filename in ("postinst", "postrm", "preinst", "prerm"))
            with open(path, "rb") as handle:
                archive.addfile(info, handle)


def make_tar_gz(source, control=False):
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.GNU_FORMAT) as archive:
            add_tree(archive, source, control=control)
    return output.getvalue()


def ar_member(name, payload):
    encoded_name = (name + "/").encode("ascii")
    header = b"".join((
        encoded_name.ljust(16),
        b"0".ljust(12),
        b"0".ljust(6),
        b"0".ljust(6),
        b"100644".ljust(8),
        str(len(payload)).encode("ascii").ljust(10),
        b"`\n",
    ))
    return header + payload + (b"\n" if len(payload) % 2 else b"")


def write_package(path, control_archive, data_archive):
    with open(path, "wb") as package:
        package.write(b"!<arch>\n")
        package.write(ar_member("debian-binary", b"2.0\n"))
        package.write(ar_member("control.tar.gz", control_archive))
        package.write(ar_member("data.tar.gz", data_archive))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", default=os.path.join(ROOT, "dist"))
    args = parser.parse_args()
    fields = read_control()
    validate_architecture_neutral_payload()
    if os.path.isdir(args.dist):
        for name in os.listdir(args.dist):
            if name.startswith(fields["Package"] + "_") and name.endswith((".deb", ".ipk")):
                os.unlink(os.path.join(args.dist, name))
    else:
        os.makedirs(args.dist)

    control_archive = make_tar_gz(CONTROL_DIR, control=True)
    data_archive = make_tar_gz(ROOTFS_DIR)
    stem = "%s_%s_all" % (fields["Package"], fields["Version"])
    outputs = []
    for extension in ("deb", "ipk"):
        path = os.path.join(args.dist, stem + "." + extension)
        write_package(path, control_archive, data_archive)
        outputs.append(path)
        print(path)
    return outputs


if __name__ == "__main__":
    main()
