from __future__ import absolute_import, division, print_function

import os
import shutil
from unittest import TestCase

import numpy as np
import pandas as pd
import pytest

from larray.tests.common import assert_array_nan_equal, inputpath
from larray import (Session, Axis, LArray, isnan, larray_equal, zeros_like, ndtest, ones_like,
                    local_arrays, global_arrays, arrays)
from larray.util.misc import pickle

try:
    import xlwings as xw
except ImportError:
    xw = None


def equal(o1, o2):
    if isinstance(o1, LArray) or isinstance(o2, LArray):
        return o1.equals(o2)
    elif isinstance(o1, Axis) or isinstance(o2, Axis):
        return o1.equals(o2)
    else:
        return o1 == o2

global_arr1 = ndtest((2, 2))
_global_arr2 = ndtest((3, 3))


class TestSession(TestCase):
    def setUp(self):
        self.a = Axis([], 'a')
        self.b = Axis([], 'b')
        self.c = 'c'
        self.d = {}
        self.e = ndtest([(2, 'a0'), (3, 'a1')])
        self.e2 = ndtest(('a=a0..a2', 'b=b0..b2'))
        self.f = ndtest([(3, 'a0'), (2, 'a1')])
        self.g = ndtest([(2, 'a0'), (4, 'a1')])
        self.session = Session([
            ('b', self.b), ('a', self.a),
            ('c', self.c), ('d', self.d),
            ('e', self.e), ('g', self.g), ('f', self.f),
        ])

    @pytest.fixture(autouse=True)
    def output_dir(self, tmpdir_factory):
        self.tmpdir = tmpdir_factory.mktemp('tmp_session').strpath

    def get_path(self, fname):
        return os.path.join(self.tmpdir, fname)

    def assertObjListEqual(self, got, expected):
        self.assertEqual(len(got), len(expected))
        for e1, e2 in zip(got, expected):
            self.assertTrue(equal(e1, e2), "{} != {}".format(e1, e2))

    def test_init(self):
        s = Session(self.b, self.a, c=self.c, d=self.d,
                    e=self.e, f=self.f, g=self.g)
        self.assertEqual(s.names, ['a', 'b', 'c', 'd', 'e', 'f', 'g'])

        s = Session(inputpath('test_session.h5'))
        self.assertEqual(s.names, ['e', 'f', 'g'])

        # this needs xlwings installed
        # s = Session('test_session_ef.xlsx')
        # self.assertEqual(s.names, ['e', 'f'])

        # TODO: format autodetection does not work in this case
        # s = Session('test_session_csv')
        # self.assertEqual(s.names, ['e', 'f', 'g'])

    def test_getitem(self):
        s = self.session
        self.assertIs(s['a'], self.a)
        self.assertIs(s['b'], self.b)
        self.assertEqual(s['c'], 'c')
        self.assertEqual(s['d'], {})

    def test_getitem_list(self):
        s = self.session
        self.assertEqual(list(s[[]]), [])
        self.assertEqual(list(s[['b', 'a']]), [self.b, self.a])
        self.assertEqual(list(s[['a', 'b']]), [self.a, self.b])
        self.assertEqual(list(s[['a', 'e', 'g']]), [self.a, self.e, self.g])
        self.assertEqual(list(s[['g', 'a', 'e']]), [self.g, self.a, self.e])

    def test_getitem_larray(self):
        s1 = self.session.filter(kind=LArray)
        s2 = Session({'e': self.e + 1, 'f': self.f})
        res_eq = s1[s1.array_equals(s2)]
        res_neq = s1[~(s1.array_equals(s2))]
        assert list(res_eq) == [self.f]
        assert list(res_neq) == [self.e, self.g]

    def test_setitem(self):
        s = self.session
        s['g'] = 'g'
        self.assertEqual(s['g'], 'g')

    def test_getattr(self):
        s = self.session
        self.assertIs(s.a, self.a)
        self.assertIs(s.b, self.b)
        self.assertEqual(s.c, 'c')
        self.assertEqual(s.d, {})

    def test_setattr(self):
        s = self.session
        s.h = 'h'
        self.assertEqual(s.h, 'h')

    def test_add(self):
        s = self.session
        h = Axis([], 'h')
        s.add(h, i='i')
        self.assertTrue(h.equals(s.h))
        self.assertEqual(s.i, 'i')

    def test_iter(self):
        expected = [self.b, self.a, self.c, self.d, self.e, self.g, self.f]
        self.assertObjListEqual(self.session, expected)

    def test_filter(self):
        s = self.session
        s.ax = 'ax'
        self.assertObjListEqual(s.filter(), [self.b, self.a, 'c', {},
                                             self.e, self.g, self.f, 'ax'])
        self.assertEqual(list(s.filter('a')), [self.a, 'ax'])
        self.assertEqual(list(s.filter('a', dict)), [])
        self.assertEqual(list(s.filter('a', str)), ['ax'])
        self.assertEqual(list(s.filter('a', Axis)), [self.a])
        self.assertEqual(list(s.filter(kind=Axis)), [self.b, self.a])
        self.assertObjListEqual(s.filter(kind=LArray), [self.e, self.g, self.f])
        self.assertEqual(list(s.filter(kind=dict)), [{}])

    def test_names(self):
        s = self.session
        self.assertEqual(s.names, ['a', 'b', 'c', 'd', 'e', 'f', 'g'])
        # add them in the "wrong" order
        s.add(i='i')
        s.add(h='h')
        self.assertEqual(s.names, ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'])

    def test_h5_io(self):
        fpath = self.get_path('test_session.h5')
        self.session.save(fpath)

        s = Session()
        s.load(fpath)
        # HDF does *not* keep ordering (ie, keys are always sorted)
        self.assertEqual(list(s.keys()), ['e', 'f', 'g'])

        # update an array (overwrite=False)
        Session(e=self.e2).save(fpath, overwrite=False)
        s.load(fpath)
        self.assertEqual(list(s.keys()), ['e', 'f', 'g'])
        assert_array_nan_equal(s['e'], self.e2)

        s = Session()
        s.load(fpath, ['e', 'f'])
        self.assertEqual(list(s.keys()), ['e', 'f'])

    def test_xlsx_pandas_io(self):
        fpath = self.get_path('test_session.xlsx')
        self.session.save(fpath, engine='pandas_excel')

        s = Session()
        s.load(fpath, engine='pandas_excel')
        self.assertEqual(list(s.keys()), ['e', 'g', 'f'])

        # update an array (overwrite=False)
        Session(e=self.e2).save(fpath, engine='pandas_excel', overwrite=False)
        s.load(fpath, engine='pandas_excel')
        self.assertEqual(list(s.keys()), ['e', 'g', 'f'])
        assert_array_nan_equal(s['e'], self.e2)

        fpath = self.get_path('test_session_ef.xlsx')
        self.session.save(fpath, ['e', 'f'], engine='pandas_excel')
        s = Session()
        s.load(fpath, engine='pandas_excel')
        self.assertEqual(list(s.keys()), ['e', 'f'])

    @pytest.mark.skipif(xw is None, reason="xlwings is not available")
    def test_xlsx_xlwings_io(self):
        fpath = self.get_path('test_session_xw.xlsx')
        # test save when Excel file does not exist
        self.session.save(fpath, engine='xlwings_excel')

        s = Session()
        s.load(fpath, engine='xlwings_excel')
        # ordering is only kept if the file did not exist previously (otherwise the ordering is left intact)
        self.assertEqual(list(s.keys()), ['e', 'g', 'f'])

        # update an array (overwrite=False)
        Session(e=self.e2).save(fpath, engine='xlwings_excel', overwrite=False)
        s.load(fpath, engine='xlwings_excel')
        self.assertEqual(list(s.keys()), ['e', 'g', 'f'])
        assert_array_nan_equal(s['e'], self.e2)

        fpath = self.get_path('test_session_ef_xw.xlsx')
        self.session.save(fpath, ['e', 'f'], engine='xlwings_excel')
        s = Session()
        s.load(fpath, engine='xlwings_excel')
        self.assertEqual(list(s.keys()), ['e', 'f'])

    def test_csv_io(self):
        try:
            fpath = self.get_path('test_session_csv')
            self.session.to_csv(fpath)

            # test loading a directory
            s = Session()
            s.load(fpath, engine='pandas_csv')
            # CSV cannot keep ordering (so we always sort keys)
            self.assertEqual(list(s.keys()), ['e', 'f', 'g'])

            # test loading with a pattern
            pattern = os.path.join(fpath, '*.csv')
            s = Session(pattern)
            # s = Session()
            # s.load(pattern)
            self.assertEqual(list(s.keys()), ['e', 'f', 'g'])

            # create an invalid .csv file
            invalid_fpath = os.path.join(fpath, 'invalid.csv')
            with open(invalid_fpath, 'w') as f:
                f.write(',",')

            # try loading the directory with the invalid file
            with pytest.raises(pd.errors.ParserError) as e_info:
                s = Session(pattern)

            # test loading a pattern, ignoring invalid/unsupported files
            s = Session()
            s.load(pattern, ignore_exceptions=True)
            self.assertEqual(list(s.keys()), ['e', 'f', 'g'])
        finally:
            shutil.rmtree(fpath)

    def test_pickle_io(self):
        fpath = self.get_path('test_session.pkl')
        self.session.save(fpath)

        s = Session()
        s.load(fpath, engine='pickle')
        self.assertEqual(list(s.keys()), ['e', 'g', 'f'])

        # update an array (overwrite=False)
        Session(e=self.e2).save(fpath, overwrite=False)
        s.load(fpath, engine='pickle')
        self.assertEqual(list(s.keys()), ['e', 'g', 'f'])
        assert_array_nan_equal(s['e'], self.e2)

    def test_to_globals(self):
        with pytest.warns(RuntimeWarning) as caught_warnings:
            self.session.to_globals()
        assert len(caught_warnings) == 1
        assert caught_warnings[0].message.args[0] == "Session.to_globals should usually only be used in interactive " \
                                                     "consoles and not in scripts. Use warn=False to deactivate this " \
                                                     "warning."
        assert caught_warnings[0].filename == __file__

        self.assertIs(a, self.a)
        self.assertIs(b, self.b)
        self.assertIs(c, self.c)
        self.assertIs(d, self.d)
        self.assertIs(e, self.e)
        self.assertIs(f, self.f)
        self.assertIs(g, self.g)

        # test inplace
        backup_dest = e
        backup_value = self.session.e.copy()
        self.session.e = zeros_like(e)
        self.session.to_globals(inplace=True, warn=False)
        # check the variable is correct (the same as before)
        self.assertIs(e, backup_dest)
        self.assertIsNot(e, self.session.e)
        # check the content has changed
        assert_array_nan_equal(e, self.session.e)
        self.assertFalse(e.equals(backup_value))

    def test_array_equals(self):
        sess = self.session.filter(kind=LArray)
        expected = Session([('e', self.e), ('f', self.f), ('g', self.g)])
        assert all(sess.array_equals(expected))

        other = Session({'e': self.e, 'f': self.f})
        res = sess.array_equals(other)
        assert res.ndim == 1
        assert res.axes.names == ['name']
        assert np.array_equal(res.axes.labels[0], ['e', 'g', 'f'])
        assert list(res) == [True, False, True]

        e2 = self.e.copy()
        e2.i[1, 1] = 42
        other = Session({'e': e2, 'f': self.f})
        res = sess.array_equals(other)
        assert res.axes.names == ['name']
        assert np.array_equal(res.axes.labels[0], ['e', 'g', 'f'])
        assert list(res) == [False, False, True]

    def test_eq(self):
        sess = self.session.filter(kind=LArray)
        expected = Session([('e', self.e), ('f', self.f), ('g', self.g)])
        assert all([array.all() for array in (sess == expected).values()])

        other = Session([('e', self.e), ('f', self.f)])
        res = sess == other
        assert list(res.keys()) == ['e', 'g', 'f']
        assert [arr.all() for arr in res.values()] == [True, False, True]

        e2 = self.e.copy()
        e2.i[1, 1] = 42
        other = Session([('e', e2), ('f', self.f)])
        res = sess == other
        assert [arr.all() for arr in res.values()] == [False, False, True]

    def test_ne(self):
        sess = self.session.filter(kind=LArray)
        expected = Session([('e', self.e), ('f', self.f), ('g', self.g)])
        assert ([(~array).all() for array in (sess != expected).values()])

        other = Session([('e', self.e), ('f', self.f)])
        res = sess != other
        assert [(~arr).all() for arr in res.values()] == [True, False, True]

        e2 = self.e.copy()
        e2.i[1, 1] = 42
        other = Session([('e', e2), ('f', self.f)])
        res = sess != other
        assert [(~arr).all() for arr in res.values()] == [False, False, True]

    def test_sub(self):
        sess = self.session.filter(kind=LArray)

        # session - session
        other = Session({'e': self.e - 1, 'f': ones_like(self.f)})
        diff = sess - other
        assert_array_nan_equal(diff['e'], np.full((2, 3), 1, dtype=np.int32))
        assert_array_nan_equal(diff['f'], self.f - ones_like(self.f))
        assert isnan(diff['g']).all()

        # session - scalar
        diff = sess - 2
        assert_array_nan_equal(diff['e'], self.e - 2)
        assert_array_nan_equal(diff['f'], self.f - 2)
        assert_array_nan_equal(diff['g'], self.g - 2)

        # session - dict(LArray and scalar)
        other = {'e': ones_like(self.e), 'f': 1}
        diff = sess - other
        assert_array_nan_equal(diff['e'], self.e - ones_like(self.e))
        assert_array_nan_equal(diff['f'], self.f - 1)
        assert isnan(diff['g']).all()

    def test_rsub(self):
        sess = self.session.filter(kind=LArray)

        # scalar - session
        diff = 2 - sess
        assert_array_nan_equal(diff['e'], 2 - self.e)
        assert_array_nan_equal(diff['f'], 2 - self.f)
        assert_array_nan_equal(diff['g'], 2 - self.g)

        # dict(LArray and scalar) - session
        other = {'e': ones_like(self.e), 'f': 1}
        diff = other - sess
        assert_array_nan_equal(diff['e'], ones_like(self.e) - self.e)
        assert_array_nan_equal(diff['f'], 1 - self.f)
        assert isnan(diff['g']).all()

    def test_div(self):
        sess = self.session.filter(kind=LArray)
        other = Session({'e': self.e - 1, 'f': self.f + 1})

        with pytest.warns(RuntimeWarning) as caught_warnings:
            res = sess / other
        assert len(caught_warnings) == 1
        assert caught_warnings[0].message.args[0] == "divide by zero encountered during operation"
        assert caught_warnings[0].filename == __file__

        with np.errstate(divide='ignore', invalid='ignore'):
            flat_e = np.arange(6) / np.arange(-1, 5)
        assert_array_nan_equal(res['e'], flat_e.reshape(2, 3))

        flat_f = np.arange(6) / np.arange(1, 7)
        assert_array_nan_equal(res['f'], flat_f.reshape(3, 2))
        self.assertTrue(isnan(res['g']).all())

    def test_rdiv(self):
        sess = self.session.filter(kind=LArray)

        # scalar / session
        res = 2 / sess
        assert_array_nan_equal(res['e'], 2 / self.e)
        assert_array_nan_equal(res['f'], 2 / self.f)
        assert_array_nan_equal(res['g'], 2 / self.g)

        # dict(LArray and scalar) - session
        other = {'e': self.e, 'f': self.f}
        res = other / sess
        assert_array_nan_equal(res['e'], self.e / self.e)
        assert_array_nan_equal(res['f'], self.f / self.f)

    def test_summary(self):
        sess = self.session.filter(kind=LArray)
        self.assertEqual(sess.summary(),
                         "e: a0*, a1*\n    \n\n"
                         "g: a0*, a1*\n    \n\n"
                         "f: a0*, a1*\n    \n")

    def test_pickle_roundtrip(self):
        original = self.session
        s = pickle.dumps(original)
        res = pickle.loads(s)
        assert res.equals(original)

    def test_local_arrays(self):
        local_arr1 = ndtest(2)
        _local_arr2 = ndtest(3)

        # exclude private local arrays
        s = local_arrays()
        s_expected = Session([('local_arr1', local_arr1)])
        assert s.equals(s_expected)

        # all local arrays
        s = local_arrays(include_private=True)
        s_expected = Session([('local_arr1', local_arr1), ('_local_arr2', _local_arr2)])
        assert s.equals(s_expected)

    def test_global_arrays(self):
        # exclude private global arrays
        s = global_arrays()
        s_expected = Session([('global_arr1', global_arr1)])
        assert s.equals(s_expected)

        # all global arrays
        s = global_arrays(include_private=True)
        s_expected = Session([('global_arr1', global_arr1), ('_global_arr2', _global_arr2)])
        assert s.equals(s_expected)

    def test_arrays(self):
        local_arr1 = ndtest(2)
        _local_arr2 = ndtest(3)

        # exclude private arrays
        s = arrays()
        s_expected = Session([('local_arr1', local_arr1), ('global_arr1', global_arr1)])
        assert s.equals(s_expected)

        # all arrays
        s = arrays(include_private=True)
        s_expected = Session([('local_arr1', local_arr1), ('_local_arr2', _local_arr2),
                              ('global_arr1', global_arr1), ('_global_arr2', _global_arr2)])
        assert s.equals(s_expected)


if __name__ == "__main__":
    pytest.main()
