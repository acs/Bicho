# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2013 GSyC/LibreSoft, Universidad Rey Juan Carlos
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#         Santiago Dueñas <sduenas@libresoft.es>
#

import csv
import os.path
import sys
import unittest

import bs4
import lxml.objectify

if not '..' in sys.path:
    sys.path.insert(0, '..')

from bicho.backends.parsers import UnmarshallingError,\
    CSVParserError, HTMLParserError, XMLParserError,\
    CSVParser, HTMLParser, XMLParser


# Name of directory where the test input files are stored
TEST_FILES_DIRNAME = 'parsers_data'

# Test files
CSV_VALID_FILE = 'csv_valid.csv'
CSV_DIALECT_FILE = 'csv_dialect.csv'
HTML_VALID_FILE = 'html_valid.html'
HTML_UTF8_FILE = 'html_utf8.html'
XML_VALID_FILE = 'xml_valid.xml'
XML_INVALID_FILE = 'xml_invalid.xml'
XML_UTF8_FILE = 'xml_utf8.xml'


def read_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
    return content


class TestUnmarshallingError(unittest.TestCase):

    def test_type(self):
        # Check whether raises a TypeError exception when
        # is not given an Exception class as third parameter
        self.assertRaises(TypeError, UnmarshallingError,
                          'Identity', True, 'invalid name',)

    def test_error_message(self):
        # Make sure that prints the correct error
        e = UnmarshallingError('Attachment')
        self.assertEqual('error unmarshalling object to Attachment.', str(e))

        e = UnmarshallingError('Identity', AttributeError())
        self.assertEqual('error unmarshalling object to Identity. AttributeError()',
                         str(e))

        e = UnmarshallingError('Identity', AttributeError(), 'Invalid email address')
        self.assertEqual('error unmarshalling object to Identity. Invalid email address. AttributeError()',
                         str(e))

        e = UnmarshallingError('Comment', cause='Invalid date')
        self.assertEqual('error unmarshalling object to Comment. Invalid date.',
                         str(e))


class TestCSVParserError(unittest.TestCase):

    def test_type(self):
        # Check whether raises a TypeError exception when
        # is not given an Exception class as first parameter
        self.assertRaises(TypeError, CSVParserError, 'error')

    def test_error_message(self):
        # Make sure that prints the correct error
        e = CSVParserError()
        self.assertEqual('error parsing CSV.', str(e))

        e = CSVParserError(Exception())
        self.assertEqual('error parsing CSV. Exception()', str(e))


class TestHTMLParserError(unittest.TestCase):

    def test_type(self):
        # Check whether raises a TypeError exception when
        # is not given an Exception class as first parameter
        self.assertRaises(TypeError, HTMLParserError, 'error')

    def test_error_message(self):
        # Make sure that prints the correct error
        e = HTMLParserError()
        self.assertEqual('error parsing HTML.', str(e))

        e = HTMLParserError(Exception())
        self.assertEqual('error parsing HTML. Exception()', str(e))


class TestCSVParser(unittest.TestCase):

    def test_readonly_properties(self):
        parser = CSVParser('', )
        self.assertRaises(AttributeError, setattr, parser, 'data', '')
        self.assertEqual(None, parser.data)

    def test_parse_invalid_type_stream(self):
        parser = CSVParser(None)
        self.assertRaises(TypeError, parser.parse)

    def test_parse_valid_csv(self):
        # Check whether it parses a valid CSV stream
        filepath = os.path.join(TEST_FILES_DIRNAME, CSV_VALID_FILE)
        content = read_file(filepath)

        parser = CSVParser(content)
        parser.parse()
        self.assertIsInstance(parser.data, csv.DictReader)

        rows = [d for d in parser.data]
        self.assertEqual(5, len(rows))

        row = rows[0]
        self.assertEqual('15', row['bug_id'])
        self.assertEqual('LibreGeoSocial (Android)', row['product'])
        self.assertEqual('general', row['component'])
        self.assertEqual('rocapal', row['assigned_to'])
        self.assertEqual('RESOLVED', row['bug_status'])
        self.assertEqual('FIXED', row['resolution'])
        # Really useful assertion, a comma is included in description
        self.assertEqual('The location service runs in GPS mode, always', row['short_desc'])
        self.assertEqual('2009-07-22 15:27:25', row['changeddate'])

        row = rows[3]
        self.assertEqual('20', row['bug_id'])
        self.assertEqual('jcaden', row['assigned_to'])
        self.assertEqual('ASSIGNED', row['bug_status'])
        self.assertEqual('---', row['resolution'])

        row = rows[4]
        self.assertEqual('carlosgc', row['assigned_to'])
        self.assertEqual('---', row['resolution'])

    def test_parse_valid_cvs_using_defined_dialect(self):
        # Check whether it parses a valid CSV stream
        # using user defined parameters
        filepath = os.path.join(TEST_FILES_DIRNAME, CSV_DIALECT_FILE)
        content = read_file(filepath)

        parser = CSVParser(content, fieldnames=['id', 'country', 'city'],
                           delimiter=';', quotechar='\'')
        self.assertEqual(['id', 'country', 'city'], parser.fieldnames)
        self.assertEqual(';', parser.delimiter)
        self.assertEqual('\'', parser.quotechar)

        parser.parse()
        rows = [d for d in parser.data]
        self.assertEqual(8, len(rows))

        row = rows[0]
        self.assertEqual('1', row['id'])
        self.assertEqual('Spain', row['country'])
        self.assertEqual('Madrid', row['city'])

        row = rows[1]
        self.assertEqual('2', row['id'])
        self.assertEqual('France', row['country'])
        self.assertEqual('Paris', row['city'])

        row = rows[2]
        self.assertEqual('10', row['id'])
        self.assertEqual('England', row['country'])
        self.assertEqual('London', row['city'])

        row = rows[5]
        self.assertEqual('201', row['id'])
        self.assertEqual('Norway', row['country'])
        self.assertEqual('Oslo', row['city'])

        row = rows[7]
        self.assertEqual('500', row['id'])
        self.assertEqual('Iceland', row['country'])
        self.assertEqual('Reykjavik', row['city'])


class TestHTMLParser(unittest.TestCase):

    def test_readonly_properties(self):
        parser = HTMLParser('<html><h1>Test</h1></html>')
        self.assertRaises(AttributeError, setattr, parser, 'data', '')
        self.assertEqual(None, parser.data)

    def test_parse_invalid_type_stream(self):
        parser = HTMLParser(None)
        self.assertRaises(TypeError, parser.parse)

    def test_parse_valid_html(self):
        # Check whether it parses a valid HTML stream
        filepath = os.path.join(TEST_FILES_DIRNAME, HTML_VALID_FILE)
        html = read_file(filepath)

        parser = HTMLParser(html)
        parser.parse()

        bug = parser.data
        self.assertIsInstance(bug, bs4.BeautifulSoup)

        self.assertEqual(u'Bug 348 \u2013 Testing KESI component', bug.title.string)
        self.assertEqual(u'Last modified: 2013-07-03 11:28:03 CEST',
                         bug.find(id='information').p.string)
        self.assertEqual(10, len(bug.find_all('table')))

    def test_parse_uf8_characters_html(self):
        # Check whether it parses a valid HTML stream that
        # contains UFT-8 characters
        filepath = os.path.join(TEST_FILES_DIRNAME, HTML_UTF8_FILE)
        html = read_file(filepath)

        parser = HTMLParser(html)
        parser.parse()
        root = parser.data

        self.assertEqual(u'sdueñas', root.h1.string)
        self.assertEqual(u'\nEn el Este, éste está,está éste en el Este, pero el Este, ¿dónde está?\n',
                         root.p.string)


class TestXMLParserError(unittest.TestCase):

    def test_type(self):
        # Check whether raises a TypeError exception when
        # is not given an Exception class as first parameter
        self.assertRaises(TypeError, XMLParserError, 'error')

    def test_error_message(self):
        # Make sure that prints the correct error
        e = XMLParserError()
        self.assertEqual('error parsing XML.', str(e))

        e = XMLParserError(Exception())
        self.assertEqual('error parsing XML. Exception()', str(e))


class TestXMLParser(unittest.TestCase):

    def test_readonly_properties(self):
        parser = XMLParser('<node id="1"/>')
        self.assertRaises(AttributeError, setattr, parser, 'data', '')
        self.assertEqual(None, parser.data)

    def test_parse_invalid_type_stream(self):
        parser = XMLParser(None)
        self.assertRaises(TypeError, parser.parse)

    def test_parse_valid_xml(self):
        # Check whether it parses a valid XML stream
        filepath = os.path.join(TEST_FILES_DIRNAME, XML_VALID_FILE)
        xml = read_file(filepath)

        parser = XMLParser(xml)
        parser.parse()

        bugs = parser.data
        self.assertIsInstance(bugs, lxml.objectify.ObjectifiedElement)

        self.assertEqual(2, len(bugs.bug))

        bug = bugs.bug[0]
        self.assertEqual('8', bug.get('id'))
        self.assertEqual('Mock bug', bug.description)
        self.assertEqual('closed', bug.status)
        self.assertEqual(2, len(bug.comment))
        self.assertEqual('1', bug.comment[0].get('id'))
        self.assertEqual('johnsmith', bug.comment[0].get('submitted_by'))
        self.assertEqual('2007-01-01', bug.comment[0].get('submitted_on'))
        self.assertEqual('A comment', bug.comment[0])
        self.assertEqual('2', bug.comment[1].get('id'))
        self.assertEqual('sduenas', bug.comment[1].get('submitted_by'))
        self.assertEqual('2013-01-01', bug.comment[1].get('submitted_on'))
        self.assertEqual('Closed', bug.comment[1])

        bug = bugs.bug[1]
        self.assertEqual("Another test bug", bug.description)
        self.assertEqual("open", bug.status)

    def test_parse_invalid_xml(self):
        # Check whether it parses an invalid XML stream
        filepath = os.path.join(TEST_FILES_DIRNAME, XML_INVALID_FILE)
        xml = read_file(filepath)

        parser = XMLParser(xml)
        self.assertRaisesRegexp(XMLParserError,
                                'error parsing XML\. XMLSyntaxError',
                                parser.parse)

    def test_parse_uf8_characters_xml(self):
        # Check whether it parses a valid XML stream that
        # contains UFT-8 characters
        filepath = os.path.join(TEST_FILES_DIRNAME, XML_UTF8_FILE)
        xml = read_file(filepath)

        parser = XMLParser(xml)
        parser.parse()
        root = parser.data

        self.assertEqual(u'sdueñas', root.comment.get('editor'))
        self.assertEqual(u'\nEn el Este, éste está,está éste en el Este, pero el Este, ¿dónde está?\n',
                         root.comment)


if __name__ == '__main__':
    unittest.main()
