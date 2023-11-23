import unittest
import os
import pytest

import tscat
from tscat.filtering import In, Field
import datetime as dt

start = dt.datetime.now()
stop = dt.datetime.now() + dt.timedelta(days=1)

tscat.base._backend = tscat.orm_sqlalchemy.Backend(testing=True)  # create a memory-database for tests


class TestPerformance(unittest.TestCase):
    def setUp(self) -> None:
        if "GITHUB_ACTION" in os.environ or os.environ.get('COVERAGE_RUN', 'false') == 'true':
            self.skipTest("skip perf-tests on GitHub and during coverage.")
        tscat.base._backend = tscat.orm_sqlalchemy.Backend(testing=True)  # create a memory-database for tests

    @pytest.mark.timeout(5)
    def test_create_events_wo_keywords_wo_context_manager(self):
        for i in range(10000):
            tscat.create_event(start, stop, author='Patrick')

    @pytest.mark.timeout(3)
    def test_create_events_wo_keywords_w_context_manager(self):
        with tscat.Session() as s:
            events = [s.create_event(start, stop, author='Patrick') for _ in range(10000)]
            c = s.create_catalogue('Test1', 'Patrick')
            s.add_events_to_catalogue(c, events)

    @pytest.mark.timeout(3)
    def test_create_events_w_keywords_w_context_manager(self):
        with tscat.Session() as s:
            events = [s.create_event(start, stop, author='Patrick', field1=1, field2=1, tags=['tag1', 'tag2']) for _ in
                      range(10000)]
            c = s.create_catalogue('TestP', 'Patrick')
            s.add_events_to_catalogue(c, events)

    @pytest.mark.timeout(3.5)
    def test_get(self):
        with tscat.Session() as s:
            events = [s.create_event(start, stop, author='Patrick', field1=1, field2=1, tags=['tag1', 'tag2']) for _ in
                      range(10000)]
            c = s.create_catalogue('TestP', 'Patrick')
            s.add_events_to_catalogue(c, events)

        c = tscat.get_catalogues()[0]
        e = tscat.get_events(c)[0]
        self.assertEqual(len(e), 10000)

    @pytest.mark.timeout(3.5)
    def test_get_filter(self):
        with tscat.Session() as s:
            events = [s.create_event(start, stop, author='Patrick', field1=1, field2=1, tags=['tag1', 'tag2']) for _ in
                      range(10000)]
            c = s.create_catalogue('TestP', 'Patrick')
            s.add_events_to_catalogue(c, events)

        e = tscat.get_events(In('tag1', Field('tags')))
        self.assertEqual(len(e), 10000)

    @pytest.mark.timeout(6)  # we create 2x 10K events
    def test_export_import_catalogue_with_many_events_shall_be_reasonably_fast(self):
        with tscat.Session() as s:
            events = [s.create_event(start, stop, author='Patrick') for _ in range(10000)]
            c = s.create_catalogue('Test1', 'Patrick')
            s.add_events_to_catalogue(c, events)

        export_blob = tscat.export_json(c)

        tscat.discard()

        tscat.import_json(export_blob)

        assert events == tscat.get_events()
        assert [c] == tscat.get_catalogues()
