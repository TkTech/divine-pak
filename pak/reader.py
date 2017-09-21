#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import zlib
import struct
from collections import namedtuple, OrderedDict

import lz4.block

# 16 bytes
PAKHeader = namedtuple('PAKHeader', [
    'version',
    'file_table_offset',
    'file_table_size',
    'archive_count',
    'unknown_2'
])

# 280 bytes
_PAKEntry = namedtuple('PAKEntry', [
    # Always 256
    'name',
    'offset',
    'size',
    'real_size',
    'archive_num',
    'flags',
    'checksum'
])


class PAKEntry(_PAKEntry):
    @property
    def is_zlib(self):
        return self.flags & 0xF == 1

    @property
    def is_lz4block(self):
        return self.flags & 0xF == 2


class PAKFileReader(object):
    #: The tail signature for a Divinity II PAK file.
    MAGIC = b'LSPK'

    def __init__(self, file_path):
        """
        """
        # A file path is required to handle split archives, otherwise
        # simply accepting file-like objects would be a better choice.
        archive = open(file_path, 'rb')
        #: All (possibly open) file handles for archive parts.
        self.archive_handles = {0: archive}
        # The naming pattern used to open subsequent file archive parts.
        self._file_name_pattern = '{0}/{1}_{{0}}.pak'.format(
            os.path.dirname(file_path),
            os.path.basename(file_path).split('.')[0]
        )

        archive.seek(-8, 2)

        # The offset in bytes from the end of the file to the start of the
        # tail.
        tail_offset = struct.unpack('<I', archive.read(4))[0]

        # PAK archives have a magic at the end of the file.
        if archive.read(4) != self.MAGIC:
            raise ValueError('Unsupported file format.')

        archive.seek(-tail_offset, 2)

        #: The loaded file header.
        self.header = PAKHeader._make(struct.unpack(
            '<IIIHH',
            archive.read(16)
        ))

        if self.header.version != 13:
            raise ValueError('Unsupported file version.')

        archive.seek(self.header.file_table_offset)

        # The # of files we should expect from the file_table.
        file_count = struct.unpack('<I', archive.read(4))[0]
        file_table = lz4.block.decompress(
            archive.read(
                # We want the complete file table, minus the 4 bytes
                # which make up the file_count.
                self.header.file_table_size - 4
            ),
            # The size of the *de*compressed block. If we don't specify
            # a value for this lz4 will assume there's a length prefix,
            # which we don't want.
            file_count * 280
        )

        self.file_table = OrderedDict()
        for file_entry in range(0, file_count):
            t = struct.unpack(
                '<256sIIIIII',
                file_table[file_entry * 280:file_entry * 280 + 280]
            )
            # File paths are padded with nulls to make them all 256
            # bytes so discard them.
            e = PAKEntry._make(
                (t[0].decode('utf-8').rstrip(u'\x00'),) + t[1:]
            )
            self.file_table[e.name] = e

    def close(self):
        """
        Close the main archive and any associated file handles.
        """
        for handle in self.archive_handles.values():
            handle.close()

    def read(self, path_or_entry):
        """
        Given a PAKEntry or a path returns the file contents.
        """
        if not isinstance(path_or_entry, PAKEntry):
            path_or_entry = self[path_or_entry]

        try:
            parent_archive = self.archive_handles[
                path_or_entry.archive_num
            ]
        except KeyError:
            parent_archive = open(self._file_name_pattern.format(
                path_or_entry.archive_num
            ), 'rb')
            self.archive_handles[path_or_entry.archive_num] = parent_archive

        parent_archive.seek(path_or_entry.offset)
        contents = parent_archive.read(path_or_entry.size)

        if path_or_entry.is_lz4block:
            return lz4.block.decompress(
                contents,
                path_or_entry.real_size
            )
        elif path_or_entry.is_zlib:
            return zlib.decompress(contents)
        else:
            return contents


    def __getitem__(self, key):
        return self.file_table[key]
