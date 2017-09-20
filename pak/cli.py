#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import zlib

import click
import lz4.block

from pak.reader import PAKFileReader


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


@click.group()
def cli():
    pass


@click.command('list')
@click.argument('archive', type=click.Path(exists=True))
def list_all(archive):
    """Print a list of all files contained within this archive.
    """
    reader = PAKFileReader(archive)
    for path in reader.file_table.keys():
        print(path)


@click.command()
@click.argument('archive', type=click.Path(exists=True))
@click.argument('path')
def extract(archive, path):
    """Extract the given path/name from the archive, piping it to stdout.
    """
    reader = PAKFileReader(archive)
    entry = reader[path]

    if entry.is_lz4block:
        sys.stdout.write(
            lz4.block.decompress(
                reader.read(entry),
                entry.real_size
            )
        )
    elif entry.is_zlib:
        sys.stdout.write(zlib.decompress(reader.read(entry)))
    else:
        sys.stdout.write(reader.read(entry))


@click.command()
@click.argument('archive', type=click.Path(exists=True))
@click.argument('path', required=False)
def details(archive, path):
    """Print detailed information for the given archive.

    If a path is provided, prints detailed information for a specific path
    within the archive.
    """
    reader = PAKFileReader(archive)
    if path:
        entry = reader[path]

        print(u'Name: {0}'.format(entry.name))
        print(u'Offset: 0x{:02X}'.format(entry.offset))
        print(u'Compressed Size: {0}'.format(sizeof_fmt(entry.size)))
        print(u'Decompressed Size: {0}'.format(sizeof_fmt(entry.real_size)))
        print(u'Sub-archive: {0}'.format(entry.archive_num))
        print(u'Flags: 0x{:02X}'.format(entry.flags))
        print(u'Checksum: 0x{:02X}'.format(entry.checksum))
        print(u'  - is_zlib: {0}'.format(entry.is_zlib))
        print(u'  - is_lz4block: {0}'.format(entry.is_lz4block))
    else:
        header = reader.header
        print(u'Version: 0x{:02X}'.format(header.version))
        print(u'File Table Offset: 0x{:02X}'.format(header.file_table_offset))
        print(u'File Table Size (compressed): {0}'.format(
            sizeof_fmt(header.file_table_size)
        ))
        print(u'File Table Count: {0}'.format(
            len(reader.file_table)
        ))
        print(u'Sub-archive count: {0}'.format(header.archive_count))


cli.add_command(list_all)
cli.add_command(extract)
cli.add_command(details)
