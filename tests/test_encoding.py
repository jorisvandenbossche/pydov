# -*- encoding: utf-8 -*-
import datetime
import os

import pandas as pd
import time
from io import open

import pytest

from owslib.fes import PropertyIsEqualTo
from pydov.search.boring import BoringSearch
from pydov.search.interpretaties import LithologischeBeschrijvingenSearch
from pydov.util.errors import XmlParseWarning

from tests.abstract import (
    service_ok,
)

from tests.test_search import (
    mp_wfs,
    wfs,
    mp_remote_describefeaturetype,
    mp_remote_md,
    mp_remote_fc,
    mp_remote_wfs_feature,
    mp_dov_xml
)

from tests.test_search_itp_lithologischebeschrijvingen import (
    location_wfs_describefeaturetype,
    location_md_metadata,
    location_fc_featurecatalogue,
    location_wfs_getfeature
)

location_dov_xml = 'tests/data/encoding/invalidcharacters.xml'

from tests.test_util_caching import (
    cache,
    nocache,
)


class TestEncoding(object):
    """Class grouping tests related to encoding issues."""

    @pytest.mark.online
    @pytest.mark.skipif(not service_ok(), reason="DOV service is unreachable")
    def test_search(self, nocache):
        """Test the search method with strange character in the output.

        Test whether the output has the correct encoding.

        Parameters
        ----------
        nocache : pytest.fixture
            Fixture to disable caching.

        """
        boringsearch = BoringSearch()
        query = PropertyIsEqualTo(
            propertyname='pkey_boring',
            literal='https://www.dov.vlaanderen.be/data/boring/1928-031159')

        df = boringsearch.search(query=query,
                                 return_fields=('pkey_boring', 'uitvoerder'))

        assert df.uitvoerder[0] == u'Societé Belge des Bétons'

    @pytest.mark.online
    @pytest.mark.skipif(not service_ok(), reason="DOV service is unreachable")
    @pytest.mark.parametrize('cache', [[datetime.timedelta(minutes=15)]],
                             indirect=['cache'])
    def test_search_cache(self, cache):
        """Test the search method with strange character in the output.

        Test whether the output has the correct encoding, both with and
        without using the cache.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.

        """
        boringsearch = BoringSearch()
        query = PropertyIsEqualTo(
            propertyname='pkey_boring',
            literal='https://www.dov.vlaanderen.be/data/boring/1928-031159')

        df = boringsearch.search(query=query,
                                 return_fields=('pkey_boring', 'uitvoerder',
                                                'mv_mtaw'))

        assert df.uitvoerder[0] == u'Societé Belge des Bétons'

        assert os.path.exists(os.path.join(
            cache.cachedir, 'boring', '1928-031159.xml'))

        df = boringsearch.search(query=query,
                                 return_fields=('pkey_boring', 'uitvoerder',
                                                'mv_mtaw'))

        assert df.uitvoerder[0] == u'Societé Belge des Bétons'

    @pytest.mark.online
    @pytest.mark.skipif(not service_ok(), reason="DOV service is unreachable")
    @pytest.mark.parametrize('cache', [[datetime.timedelta(minutes=15)]],
                             indirect=['cache'])
    def test_caching(self, cache):
        """Test the caching of an XML containing strange characters.

        Test whether the data is saved in the cache.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '1995-056089.xml')

        cache.clean()
        assert not os.path.exists(cached_file)

        cache.get('https://www.dov.vlaanderen.be/data/boring/1995-056089.xml')
        assert os.path.exists(cached_file)

        with open(cached_file, 'r', encoding='utf-8') as cf:
            cached_data = cf.read()
            assert cached_data != ""

        first_download_time = os.path.getmtime(cached_file)

        time.sleep(0.5)
        cache.get('https://www.dov.vlaanderen.be/data/boring/1995-056089.xml')
        # assure we didn't redownload the file:
        assert os.path.getmtime(cached_file) == first_download_time

    @pytest.mark.online
    @pytest.mark.skipif(not service_ok(), reason="DOV service is unreachable")
    @pytest.mark.parametrize('cache', [[datetime.timedelta(minutes=15)]],
                             indirect=['cache'])
    def test_save_content(self, cache):
        """Test the caching of an XML containing strange characters.

        Test if the contents of the saved document are the same as the
        original data.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '1995-056089.xml')

        cache.remove()
        assert not os.path.exists(cached_file)

        ref_data = cache.get(
            'https://www.dov.vlaanderen.be/data/boring/1995-056089.xml')
        assert os.path.exists(cached_file)

        with open(cached_file, 'r', encoding='utf-8') as cached:
            cached_data = cached.read().encode('utf-8')

        assert cached_data == ref_data

    @pytest.mark.online
    @pytest.mark.skipif(not service_ok(), reason="DOV service is unreachable")
    @pytest.mark.parametrize('cache', [[datetime.timedelta(minutes=15)]],
                             indirect=['cache'])
    def test_reuse_content(self, cache):
        """Test the caching of an XML containing strange characters.

        Test if the contents returned by the cache are the same as the
        original data.

        Parameters
        ----------
        cache : pytest.fixture providing  pydov.util.caching.TransparentCache
            TransparentCache using a temporary directory and a maximum age
            of 1 second.

        """
        cached_file = os.path.join(
            cache.cachedir, 'boring', '1995-056089.xml')

        cache.remove()
        assert not os.path.exists(cached_file)

        ref_data = cache.get(
            'https://www.dov.vlaanderen.be/data/boring/1995-056089.xml')
        assert os.path.exists(cached_file)

        cached_data = cache.get(
            'https://www.dov.vlaanderen.be/data/boring/1995-056089.xml')

        assert cached_data == ref_data

    def test_search_invalidxml_single(
            self, mp_wfs, mp_remote_describefeaturetype, mp_remote_md,
            mp_remote_fc, mp_remote_wfs_feature, mp_dov_xml, nocache):
        """Test the search method when the XML is invalid.

        If lxml is installed, the XML should parse regardless of invalid
        characters. If lxml is not installed, the dataframe should be
        returned with a warning that it will be incomplete.

        Parameters
        ----------
        mp_wfs : pytest.fixture
            Monkeypatch the call to the remote GetCapabilities request.
        mp_remote_describefeaturetype : pytest.fixture
            Monkeypatch the call to a remote DescribeFeatureType.
        mp_remote_md : pytest.fixture
            Monkeypatch the call to get the remote metadata.
        mp_remote_fc : pytest.fixture
            Monkeypatch the call to get the remote feature catalogue.
        mp_remote_wfs_feature : pytest.fixture
            Monkeypatch the call to get WFS features.
        mp_dov_xml : pytest.fixture
            Monkeypatch the call to get the remote XML data.
        nocache : pytest.fixture
            Fixture to disable caching.

        """
        lithosearch = LithologischeBeschrijvingenSearch()
        query = PropertyIsEqualTo(
            propertyname='pkey_interpretatie',
            literal='https://www.dov.vlaanderen.be/data/interpretatie/'
                    '1987-070909')

        try:
            import lxml
            have_lxml = True
        except ImportError:
            have_lxml = False

        if have_lxml:
            df = lithosearch.search(query=query)
            assert df.beschrijving[1].startswith(u'homogene groene zanden')
        else:
            with pytest.warns(XmlParseWarning):
                df = lithosearch.search(query=query)
                assert len(df) == 1
                assert pd.isnull(df.diepte_laag_van[0])
                assert pd.isnull(df.diepte_laag_tot[0])
                assert pd.isnull(df.beschrijving[0])