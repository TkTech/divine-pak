# -*- coding: utf-8 -*-
import struct
from collections import namedtuple


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def parse_stats(fin):
    from pyparsing import (
        LineEnd,
        Forward,
        Word,
        alphas,
        QuotedString,
        Group,
        OneOrMOre
    )

    EOL = LineEnd().suppress()

    new_stmt = Forward().setName('new statement')
    new_stmt << (
        Word('new').suppress() +
        Word(alphas) +
        QuotedString('"')
    ) + EOL

    data_stmt = Forward().setName('data statement')
    data_stmt << (
        Word('data').suppress() +
        QuotedString('"') +
        QuotedString('"')
    ) + EOL

    p = OneOrMore(
        Group(
            new_stmt +
            Group(
                OneOrMore(
                    data_stmt
                )
            )
        )
    )

    results = p.parseFile(fin)

    for row in results:
        action, name, data = row
        data = dict(chunks(data, 2))
        yield (action, name, data)


LSBHeader = namedtuple('LSBHeader', [
    'magic',
    'length',
    'endianness',
    'unknown_1',
    # Wiki incorrectly has this as a uin32_t instead of a uint64_t!
    'created_timestamp',
    'version_major',
    'version_minor',
    'version_build',
    'version_rev'
])


def _read_localized_string(fin):
    default_length = struct.unpack('<I', fin.read(4))[0]
    default, handle_length = struct.unpack(
        '<{0}sI'.format(
            default_length
        ),
        fin.read(default_length + 4)
    )
    handle = struct.unpack(
        '<{0}s'.format(handle_length),
        fin.read(handle_length)
    )[0]

    return (
        default.decode('utf-8').rstrip(u'\x00'),
        handle.rstrip('\x00')
    )


def _read_prefix_string(fin):
    return fin.read(
        struct.unpack('<I', fin.read(4))[0]
    ).decode('utf-8').rstrip('\x00')


def _read_node(fin, identifier_table):
    identifier, num_attrib, num_child = struct.unpack(
        '<III',
        fin.read(12)
    )

    attributes = {}
    for i in xrange(0, num_attrib):
        identifier, type_ = struct.unpack(
            '<II',
            fin.read(8)
        )
        attributes[identifier_table[identifier]] = {
            0x05: lambda f: struct.unpack('<I', f.read(4))[0],
            0x13: lambda f: struct.unpack('<?', f.read(1))[0],
            0x16: _read_prefix_string,
            0x17: _read_prefix_string,
            0x1C: _read_localized_string
        }[type_](fin)

    attributes['_children'] = children = []
    for i in xrange(0, num_child):
        children.append(_read_node(fin, identifier_table))

    return {
        identifier_table[identifier]: attributes
    }


def parse_lsb(fin):
    """
    Utility to read Larian Studio's LSB file format, which is a
    psuedo-binary XML format.
    """
    header = LSBHeader._make(
        struct.unpack(
            '<IIIIQIIII',
            fin.read(40)
        )
    )

    identifier_count = struct.unpack('<I', fin.read(4))[0]
    identifier_table = {}
    for identifier in xrange(0, identifier_count):
        length = struct.unpack('<I', fin.read(4))[0]
        name, key = struct.unpack(
            '<{0}sI'.format(length),
            fin.read(length + 4)
        )
        identifier_table[key] = name

    region_count = struct.unpack('<I', fin.read(4))[0]
    region_table = {}
    for region in xrange(0, region_count):
        key, value = struct.unpack('<II', fin.read(8))
        region_table[identifier_table[key]] = value

    regions = {}
    for region_name, region_offset in region_table.iteritems():
        fin.seek(region_offset)
        regions[region_name] = _read_node(fin, identifier_table)

    return regions
