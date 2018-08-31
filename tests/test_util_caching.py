"""Module grouping tests for the pydov.util.caching module."""
import datetime
import os
import tempfile
from io import open

import time

import pytest

import pydov
from pydov.util.caching import TransparentCache


@pytest.fixture
def mp_remote_xml(monkeypatch):
    """Monkeypatch the call to get the remote Boring XML data.

    Parameters
    ----------
    monkeypatch : pytest.fixture
        PyTest monkeypatch fixture.

    """

    def _get_remote_data(*args, **kwargs):
        with open('tests/data/types/boring/boring.xml', 'r') as f:
            data = f.read()
            if type(data) is not bytes:
                data = data.encode('utf-8')
        return data

    monkeypatch.setattr(pydov.util.caching.TransparentCache,
                        '_get_remote', _get_remote_data)


@pytest.fixture
def cache():
    transparent_cache = TransparentCache(
        cachedir=os.path.join(tempfile.gettempdir(), 'pydov_tests'),
        max_age=datetime.timedelta(seconds=1))
    yield transparent_cache

    transparent_cache.remove()


def nocache(func):
    """Decorator to temporarily disable caching.

    Parameters
    ----------
    func : function
        Function to decorate.

    """
    def wrapper(*args, **kwargs):
        orig_cache = pydov.cache
        pydov.cache = None
        func(*args, **kwargs)
        pydov.cache = orig_cache
    return wrapper


class TestTransparentCache(object):
    """Class grouping tests for the pydov.util.caching.TransparentCache
    class."""

    def test_clean(self, cache, mp_remote_xml):
        """Test the clean method.

        Test whether the cached file and the cache directory are nonexistent
        after the clean method has been called.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.
        mp_remote_xml : pytest.fixture
            Monkeypatch the call to the remote DOV service returning an XML
            document.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '2004-103984.xml')

        cache.get('https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        assert os.path.exists(cached_file)

        cache.clean()
        assert os.path.exists(cached_file)
        assert os.path.exists(cache.cachedir)

        time.sleep(1.5)
        cache.clean()
        assert not os.path.exists(cached_file)
        assert os.path.exists(cache.cachedir)

    def test_remove(self, cache, mp_remote_xml):
        """Test the remove method.

        Test whether the cache directory is nonexistent after the remove
        method has been called.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.
        mp_remote_xml : pytest.fixture
            Monkeypatch the call to the remote DOV service returning an XML
            document.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '2004-103984.xml')

        cache.get('https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        assert os.path.exists(cached_file)

        cache.remove()
        assert not os.path.exists(cached_file)
        assert not os.path.exists(cache.cachedir)

    def test_get_save(self, cache, mp_remote_xml):
        """Test the get method.

        Test whether the document is saved in the cache.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.
        mp_remote_xml : pytest.fixture
            Monkeypatch the call to the remote DOV service returning an XML
            document.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '2004-103984.xml')

        cache.clean()
        assert not os.path.exists(cached_file)

        cache.get('https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        assert os.path.exists(cached_file)

    def test_get_reuse(self, cache, mp_remote_xml):
        """Test the get method.

        Test whether the document is saved in the cache and reused in a
        second function call.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.
        mp_remote_xml : pytest.fixture
            Monkeypatch the call to the remote DOV service returning an XML
            document.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '2004-103984.xml')

        cache.clean()
        assert not os.path.exists(cached_file)

        cache.get('https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        assert os.path.exists(cached_file)

        first_download_time = os.path.getmtime(cached_file)

        time.sleep(0.5)
        cache.get('https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        # assure we didn't redownload the file:
        assert os.path.getmtime(cached_file) == first_download_time

    def test_get_invalid(self, cache, mp_remote_xml):
        """Test the get method.

        Test whether the document is saved in the cache not reused if the
        second function call is after the maximum age of the cached file.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.
        mp_remote_xml : pytest.fixture
            Monkeypatch the call to the remote DOV service returning an XML
            document.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '2004-103984.xml')

        cache.clean()
        assert not os.path.exists(cached_file)

        cache.get('https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        assert os.path.exists(cached_file)

        first_download_time = os.path.getmtime(cached_file)

        time.sleep(1.5)
        cache.get('https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        # assure we did redownload the file, since original is invalid now:
        assert os.path.getmtime(cached_file) > first_download_time

    def test_save_content(self, cache, mp_remote_xml):
        """Test whether the data is saved in the cache.

        Test if the contents of the saved document are the same as the
        original data.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.
        mp_remote_xml : pytest.fixture
            Monkeypatch the call to the remote DOV service returning an XML
            document.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '2004-103984.xml')

        cache.clean()
        assert not os.path.exists(cached_file)

        cache.get('https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        assert os.path.exists(cached_file)

        with open('tests/data/types/boring/boring.xml', 'r',
                  encoding='utf-8') as ref:
            ref_data = ref.read()

        with open(cached_file, 'r', encoding='utf-8') as cached:
            cached_data = cached.read()

        assert cached_data == ref_data

    def test_reuse_content(self, cache, mp_remote_xml):
        """Test whether the saved data is reused.

        Test if the contents returned by the cache are the same as the
        original data.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.
        mp_remote_xml : pytest.fixture
            Monkeypatch the call to the remote DOV service returning an XML
            document.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '2004-103984.xml')

        cache.clean()
        assert not os.path.exists(cached_file)

        cache.get('https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        assert os.path.exists(cached_file)

        with open('tests/data/types/boring/boring.xml', 'r') as ref:
            ref_data = ref.read().encode('utf-8')

        cached_data = cache.get(
            'https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')

        assert cached_data == ref_data

    def test_return_type(self, cache, mp_remote_xml):
        """The the return type of the get method.

        Test wether the get method returns the data in the same datatype (
        i.e. bytes) regardless of the data was cached or not.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.
        mp_remote_xml : pytest.fixture
            Monkeypatch the call to the remote DOV service returning an XML
            document.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '2004-103984.xml')

        cache.clean()
        assert not os.path.exists(cached_file)

        ref_data = cache.get(
            'https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        assert type(ref_data) is bytes

        assert os.path.exists(cached_file)

        cached_data = cache.get(
            'https://www.dov.vlaanderen.be/data/boring/2004-103984.xml')
        assert type(cached_data) is bytes
