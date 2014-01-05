# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2013 GSyC/LibreSoft, Universidad Rey Juan Carlos
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

import os.path
import tempfile
import shutil 
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from bicho.backends import Backend, BackendManager, BackendImportError, BackendDoesNotExist


# Name of directory where the test input files are stored
TEST_FILES_DIRNAME = 'backend_manager'

# Directory names for testing cases
EMPTY_DIRNAME = 'empty'
NO_PYTHON_PACKAGE_DIRNAME = 'no_package'
NO_PACKAGES_DIRNAME = 'without_packages'
EMPTY_PACKAGE_DIRNAME = 'empty_package'
INVALID_BACKEND_DIRNAME = 'invalid'
ANOTHER_INVALID_BACKEND_DIRNAME = 'invalid2'
BACKENDS_DIRNAME = 'test_backends'
ALT_BACKENDS_DIRNAME = 'alt_backends'


class TestBackendImportError(unittest.TestCase):

    def test_type(self):
        # Check whether raises a TypeError exception when
        # is not given an Exception class as second parameter
        self.assertRaises(TypeError, BackendImportError, 'test', 0)

    def test_error_message(self):
        # Make sure that prints the correct error
        e = BackendImportError('test1')
        self.assertEqual('error importing backend test1.', str(e))

        e = BackendImportError('test2', Exception())
        self.assertEqual('error importing backend test2. Exception()', str(e))


class TestBackendDoesNotExist(unittest.TestCase):

    def test_error_message(self):
        # Make sure that prints the correct error
        e = BackendDoesNotExist('test')
        self.assertEqual('backend test not found.', str(e))


class TestBackendManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a temporary directory to store the
        # inputs for the test cases
        cls.testpath = tempfile.mkdtemp(prefix='bicho_')

        # Setup an empty directory
        os.mkdir(os.path.join(cls.testpath, EMPTY_DIRNAME))

        # Setup a directory that is not a package
        dirpath = os.path.join(cls.testpath, NO_PYTHON_PACKAGE_DIRNAME,
                               NO_PYTHON_PACKAGE_DIRNAME)
        os.makedirs(dirpath)
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'note.txt'),
                    dirpath)
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'text.txt'),
                    dirpath)
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'test_backends.py'),
                    dirpath)

        # Setup a directory not containing packages
        dirpath = os.path.join(cls.testpath, NO_PACKAGES_DIRNAME,
                               NO_PACKAGES_DIRNAME)
        os.makedirs(dirpath)
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'text.txt'),
                    dirpath)
        os.mkdir(os.path.join(dirpath, 'dir1'))
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'test_backends.py'),
                    os.path.join(dirpath, 'dir1'))
        os.mkdir(os.path.join(dirpath, 'dir2'))

        # Setup a package not containing backends
        dirpath = os.path.join(cls.testpath, EMPTY_PACKAGE_DIRNAME,
                               EMPTY_PACKAGE_DIRNAME)
        os.makedirs(dirpath)
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'empty.py'),
                    os.path.join(dirpath, '__init__.py'))
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'text.txt'),
                    dirpath)
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'test_backends.py'),
                    dirpath)

        # Setup a directory containing an invalid backend
        dirpath = os.path.join(cls.testpath, INVALID_BACKEND_DIRNAME,
                               INVALID_BACKEND_DIRNAME)
        os.makedirs(dirpath)
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'invalid.py'),
                    os.path.join(dirpath, '__init__.py'))

        # Setup another directory containing an invalid backend
        dirpath = os.path.join(cls.testpath, ANOTHER_INVALID_BACKEND_DIRNAME,
                               ANOTHER_INVALID_BACKEND_DIRNAME)
        os.makedirs(dirpath)
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'invalid.py'),
                    os.path.join(dirpath, '__init__.py'))

        # Setup the backends test directory
        dirpath = os.path.join(cls.testpath, BACKENDS_DIRNAME,
                               BACKENDS_DIRNAME)
        os.makedirs(dirpath)
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'test_backends.py'),
                    os.path.join(dirpath, '__init__.py'))
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'alt_backends.py'),
                    dirpath)

        # Setup a second backend directory
        dirpath = os.path.join(cls.testpath, ALT_BACKENDS_DIRNAME,
                               ALT_BACKENDS_DIRNAME)
        os.makedirs(dirpath)
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'alt_backends.py'),
                    os.path.join(dirpath, '__init__.py'))
        shutil.copy(os.path.join(TEST_FILES_DIRNAME, 'other_backends.py'),
                    dirpath)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.testpath)

    def test_readonly_properties(self):
        dirpath = os.path.join(self.testpath, EMPTY_DIRNAME)
        manager = BackendManager(path=dirpath, debug=True)

        self.assertRaises(AttributeError, setattr, manager, 'path', '')
        self.assertEqual(dirpath, manager.path)

        self.assertRaises(AttributeError, setattr, manager, 'debug', False)
        self.assertEqual(True, manager.debug)

        self.assertRaises(AttributeError, setattr, manager, 'backends', '')
        self.assertListEqual([], manager.backends)

    def test_empty_dir(self):
        # Make sure the manager neither fails nor imports any backend from
        # an empty directory
        dirpath = os.path.join(self.testpath, EMPTY_DIRNAME)
        manager = BackendManager(path=dirpath)
        self.assertListEqual([], manager.backends)

    def test_no_python_package(self):
        # Check if the manager does not import any backend from
        # a directory that is not a python package
        dirpath = os.path.join(self.testpath, NO_PYTHON_PACKAGE_DIRNAME)
        manager = BackendManager(path=dirpath)
        self.assertListEqual([], manager.backends)

    def test_dir_without_packages(self):
        # Check whether the manager nor import any backend from a directory
        # that does not contain packages
        dirpath = os.path.join(self.testpath, NO_PACKAGES_DIRNAME)
        manager = BackendManager(path=dirpath)
        self.assertListEqual([], manager.backends)

    def test_empty_package(self):
        # Check if the manager does not import any backend from
        # a package that does not store backends in __init__.py file
        dirpath = os.path.join(self.testpath, EMPTY_PACKAGE_DIRNAME)
        manager = BackendManager(path=dirpath)
        self.assertListEqual([], manager.backends)

    def test_invalid_python_module(self):
        # In debug mode, prints an error when trying to import
        # an invalid backend
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('need to run in buffered mode')

        dirpath = os.path.join(self.testpath, INVALID_BACKEND_DIRNAME)
        manager = BackendManager(path=dirpath)
        output = sys.stdout.getvalue().strip()
        self.assertRegexpMatches(output, 'error importing backend invalid')
        self.assertListEqual([], manager.backends)

    def test_invalid_python_module_debug_mode(self):
        # Raises an BackendImportError exception trying to
        # import an invalid backend
        dirpath = os.path.join(self.testpath, ANOTHER_INVALID_BACKEND_DIRNAME)
        self.assertRaises(BackendImportError, BackendManager,
                          path=dirpath, debug=True)

    def test_backends_package(self):
        # Test whether the manager imports all the backends of a package
        dirpath = os.path.join(self.testpath, BACKENDS_DIRNAME)
        manager = BackendManager(path=dirpath)
        backends = manager.backends
        backends.sort()
        self.assertListEqual(['A', 'B'] , backends)

    def test_backends_not_in_init(self):
        # Test if the manager only imports those backends
        # stored in __init__.py and not in other modules
        dirpath = os.path.join(self.testpath,  ALT_BACKENDS_DIRNAME)
        manager = BackendManager(path=dirpath)
        backends = manager.backends
        backends.sort()
        self.assertListEqual(['C'] , backends)

    def test_subdirs(self):
        # Make sure the manager does not fail loading backends
        # from a tree of directories
        manager = BackendManager(path=self.testpath)
        backends = manager.backends
        backends.sort()
        self.assertListEqual(['A', 'B', 'C'], backends)

    def test_get(self):
        dirpath = os.path.join(self.testpath, BACKENDS_DIRNAME)
        manager = BackendManager(path=dirpath)

        backend = manager.get('B')
        self.assertIsInstance(backend, Backend)
        self.assertEqual('B', backend.name)

        self.assertRaises(BackendDoesNotExist, manager.get, 'H')

    def test_get_sequence(self):
        dirpath = os.path.join(self.testpath, BACKENDS_DIRNAME)
        manager = BackendManager(path=dirpath)

        backend = manager.get('A')
        self.assertIsInstance(backend, Backend)
        self.assertEqual('A', backend.name)

        self.assertRaises(BackendDoesNotExist, manager.get, 'Z')

        backend = manager.get('B')
        self.assertIsInstance(backend, Backend)
        self.assertEqual('B', backend.name)

        backend = manager.get('A')
        self.assertIsInstance(backend, Backend)
        self.assertEqual('A', backend.name)

        self.assertRaises(BackendDoesNotExist, manager.get, 'C')

        backend = manager.get('A')
        self.assertIsInstance(backend, Backend)
        self.assertEqual('A', backend.name)

        backend = manager.get('B')
        self.assertIsInstance(backend, Backend)
        self.assertEqual('B', backend.name)

        backend = manager.get('B')
        self.assertIsInstance(backend, Backend)
        self.assertEqual('B', backend.name)

    def test_check_backends(self):
        # Test whether all objects imported are instances of Backend
        dirpath = os.path.join(self.testpath, BACKENDS_DIRNAME)
        manager = BackendManager(path=dirpath)
        backends = manager.backends

        for b in backends:
            obj = manager.get(b)
            self.assertIsInstance(obj, Backend)


if __name__ == '__main__':
    unittest.main(buffer=True, exit=False)
