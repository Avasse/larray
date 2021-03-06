﻿New features
------------

* viewer: added a menu bar with the ability to clear the current session, save all its arrays to a file (.h5, .xlsx,
  or a directory containing multiple .csv files), and load arrays from such a file (closes :issue:`88`).

  WARNING: Only array objects are currently saved. It means that scalars, functions or others non-LArray objects
  defined in the console are *not* saved in the file.

* implemented a new describe() method on arrays to give quick summary statistics. By default, it includes the number of
  non-NaN values, the mean, standard deviation, minimum, 25, 50 and 75 percentiles and maximum.

    >>> arr = ndrange('gender=Male,Female;year=2014..2020').astype(float)
    >>> arr
    gender\year | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020
           Male |  0.0 |  1.0 |  2.0 |  3.0 |  4.0 |  5.0 |  6.0
         Female |  7.0 |  8.0 |  9.0 | 10.0 | 11.0 | 12.0 | 13.0
    >>> arr.describe()
    statistic | count | mean |               std | min |  25% | 50% |  75% |  max
              |  14.0 |  6.5 | 4.031128874149275 | 0.0 | 3.25 | 6.5 | 9.75 | 13.0

  an optional keyword argument allows to specify different percentiles to include

    >>> arr.describe(percentiles=[20, 40, 60, 80])
    statistic | count | mean |               std | min | 20% | 40% | 60% |  80% |  max
              |  14.0 |  6.5 | 4.031128874149275 | 0.0 | 2.6 | 5.2 | 7.8 | 10.4 | 13.0

  its sister method, describe_by() was also implemented to give quick summary statistics along axes or groups.

    >>> arr.describe_by('gender')
    gender\statistic | count | mean | std | min | 25% |  50% |  75% |  max
                Male |   7.0 |  3.0 | 2.0 | 0.0 | 1.5 |  3.0 |  4.5 |  6.0
              Female |   7.0 | 10.0 | 2.0 | 7.0 | 8.5 | 10.0 | 11.5 | 13.0
    >>> arr.describe_by('gender', (x.year[:2015], x.year[2019:]))
    gender | year\statistic | count | mean | std |  min |   25% |  50% |   75% |  max
      Male |          :2015 |   2.0 |  0.5 | 0.5 |  0.0 |  0.25 |  0.5 |  0.75 |  1.0
      Male |          2019: |   2.0 |  5.5 | 0.5 |  5.0 |  5.25 |  5.5 |  5.75 |  6.0
    Female |          :2015 |   2.0 |  7.5 | 0.5 |  7.0 |  7.25 |  7.5 |  7.75 |  8.0
    Female |          2019: |   2.0 | 12.5 | 0.5 | 12.0 | 12.25 | 12.5 | 12.75 | 13.0

  This closes :issue:`184`.

* implemented reindex allowing to change the order of labels and add/remove some of them to one or several axes:

    >>> arr = ndtest((2, 2))
    >>> arr
    a\b | b0 | b1
     a0 |  0 |  1
     a1 |  2 |  3
    >>> arr.reindex(x.b, ['b1', 'b2', 'b0'], fill_value=-1)
    a\b | b1 | b2 | b0
     a0 |  1 | -1 |  0
     a1 |  3 | -1 |  2
    >>> a = Axis('a', ['a1', 'a2', 'a0'])
    >>> b = Axis('b', ['b2', 'b1', 'b0'])
    >>> arr.reindex({'a': a, 'b': b}, fill_value=-1)
    a\b | b2 | b1 | b0
     a1 | -1 |  3 |  2
     a2 | -1 | -1 | -1
     a0 | -1 |  1 |  0

  using reindex one can make an array compatible with another array which has more/less labels or with labels in a
  different order:

    >>> arr2 = ndtest((3, 3))
    >>> arr2
    a\b | b0 | b1 | b2
     a0 |  0 |  1 |  2
     a1 |  3 |  4 |  5
     a2 |  6 |  7 |  8
    >>> arr.reindex(arr2.axes, fill_value=0)
    a\b | b0 | b1 | b2
     a0 |  0 |  1 |  0
     a1 |  2 |  3 |  0
     a2 |  0 |  0 |  0
    >>> arr.reindex(arr2.axes, fill_value=0) + arr2
    a\b | b0 | b1 | b2
     a0 |  0 |  2 |  2
     a1 |  5 |  7 |  5
     a2 |  6 |  7 |  8

  This closes :issue:`18`.

* added load_example_data function to load datasets used in tutorial and be able to reproduce examples. The name of the
  dataset must be provided as argument (there is currently only one available dataset). Datasets are returned as
  Session objects:

    >>> demo = load_example_data('demography')
    >>> demo.pop.info
    26 x 3 x 121 x 2 x 2
     time [26]: 1991 1992 1993 ... 2014 2015 2016
     geo [3]: 'BruCap' 'Fla' 'Wal'
     age [121]: 0 1 2 ... 118 119 120
     sex [2]: 'M' 'F'
     nat [2]: 'BE' 'FO'
    >>> demo.qx.info
    26 x 3 x 121 x 2 x 2
     time [26]: 1991 1992 1993 ... 2014 2015 2016
     geo [3]: 'BruCap' 'Fla' 'Wal'
     age [121]: 0 1 2 ... 118 119 120
     sex [2]: 'M' 'F'
     nat [2]: 'BE' 'FO'

  (closes :issue:`170`)

* implemented Axis.union, intersection and difference which produce new axes by combining the labels of the axis
  with the other labels.

    >>> letters = Axis('letters=a,b')
    >>> letters.union(Axis('letters=b,c'))
    Axis(['a', 'b', 'c'], 'letters')
    >>> letters.union(['b', 'c'])
    Axis(['a', 'b', 'c'], 'letters')
    >>> letters.intersection(['b', 'c'])
    Axis(['b'], 'letters')
    >>> letters.difference(['b', 'c'])
    Axis(['a'], 'letters')

* implemented Group.union, intersection and difference which produce new groups by combining the labels of the group
  with the other labels.

    >>> letters = Axis('letters=a..d')
    >>> letters['a', 'b'].union(letters['b', 'c'])
    letters['a', 'b', 'c'].set()
    >>> letters['a', 'b'].union(['b', 'c'])
    letters['a', 'b', 'c'].set()
    >>> letters['a', 'b'].intersection(['b', 'c'])
    letters['b'].set()
    >>> letters['a', 'b'].difference(['b', 'c'])
    letters['a'].set()

* viewer: added possibility to delete an array by pressing Delete on keyboard (closes :issue:`116`).

* Excel sheets in workbooks opened via open_excel can be renamed by changing their .name attribute:

    >>> wb = open_excel()
    >>> wb['old_sheet_name'].name = 'new_sheet_name'

* Excel sheets in workbooks opened via open_excel can be deleted using "del":

    >>> wb = open_excel()
    >>> del wb['sheet_name']

* implemented PGroup.set() to transform a positional group to an LSet.

    >>> a = Axis('a=a0..a5')
    >>> a.i[:2].set()
    a['a0', 'a1'].set()

.. _misc:

Miscellaneous improvements
--------------------------

* inverted `name` and `labels` arguments when creating an Axis and made `name` argument optional (to create anonymous
  axes). Now, it is also possible to create an Axis by passing a single string of the kind 'name=labels':

    >>> anonymous = Axis('0..100')
    >>> age = Axis('age=0..100')
    >>> gender = Axis('M,F', 'gender')

  (closes :issue:`152`)

* renamed Session.dump, dump_hdf, dump_excel and dump_csv to save, to_hdf, to_excel and to_csv (closes :issue:`217`).

* changed default value of `ddof` argument for var and std functions from 0 to 1 (closes :issue:`190`).

* implemented a new syntax for stack(): `stack({label1: value1, label2: value2}, axis)`

    >>> nat = Axis('nat', 'BE, FO')
    >>> sex = Axis('sex', 'M, F')
    >>> males = ones(nat)
    >>> males
    nat |  BE |  FO
        | 1.0 | 1.0
    >>> females = zeros(nat)
    >>> females
    nat |  BE |  FO
        | 0.0 | 0.0

  In the case the axis has already been defined in a variable, this gives:

    >>> stack({'M': males, 'F': females}, sex)
    nat\sex |   M |   F
         BE | 1.0 | 0.0
         FO | 1.0 | 0.0

  Additionally, axis can now be an axis string definition in addition to an Axis object, which means one can write this:

    >>> stack({'M': males, 'F': females}, 'sex=M,F')

  It is better than the simpler but *highly discouraged* alternative:

    >>> stack([males, females), sex)

  because it is all too easy to invert labels. It is very hard to spot the error in the following line, and larray
  cannot spot it for you either:

    >>> stack([females, males), sex)
    nat\sex |   M |   F
         BE | 0.0 | 1.0
         FO | 0.0 | 1.0

  When creating an axis from scratch (it does not already exist in a variable), one might want to use this:

    >>> stack([males, females], 'sex=M,F')

  even if this could suffer, to a lesser extent, the same problem as above when stacking many arrays.

* handle ... in transpose method to avoid having to list all axes. This can be useful, for example, to change which
  axis is displayed in columns (closes :issue:`188`).

    >>> arr.transpose(..., 'time')
    >>> arr.transpose('gender', ..., 'time')

* made scalar Groups behave even more like their value: any method available on the value is available on the Group.
  For example, if the Group has a string value, the string methods are available on it (closes :issue:`202`).

    >>> test = Axis('test', ['abc', 'a1-a2'])
    >>> test.i[0].upper()
    'ABC'
    >>> test.i[1].split('-')
    ['a1', 'a2']

* updated AxisCollection.replace so as to replace one, several or all axes and to accept axis definitions as new axes.

    >>> arr = ndtest((2, 3))
    >>> axes = arr.axes
    >>> axes
    AxisCollection([
        Axis(['a0', 'a1'], 'a'),
        Axis(['b0', 'b1', 'b2'], 'b')
    ])
    >>> row = Axis(['r0', 'r1'], 'row')
    >>> column = Axis(['c0', 'c1', 'c2'], 'column')

    Replace several axes (keywords, list of tuple or dictionary)

    >>> axes.replace(a=row, b=column)
    >>> # or
    >>> axes.replace(a="row=r0,r1", b="column=c0,c1,c2")
    >>> # or
    >>> axes.replace([(x.a, row), (x.b, column)])
    >>> # or
    >>> axes.replace({x.a: row, x.b: column})
    AxisCollection([
        Axis(['r0', 'r1'], 'row'),
        Axis(['c0', 'c1', 'c2'], 'column')
    ])

* added possibility to delete an array from a session:

    >>> s = Session({'a': ndtest((3, 3)), 'b': ndtest((2, 4)), 'c': ndtest((4, 2))})
    >>> s.names
    ['a', 'b', 'c']
    >>> del s.b
    >>> del s['c']
    >>> s.names
    ['a']

* made create_sequential axis argument accept axis definitions in addition to Axis objects like, for example, using a
  string definition (closes :issue:`160`).

    >>> create_sequential('year=2016..2019')
    year | 2016 | 2017 | 2018 | 2019
         |    0 |    1 |    2 |    3

* replaced \*args, \**kwargs by explicit arguments in documentation of aggregation functions (sum, prod, mean, std,
  var, ...). Closes :issue:`41`.

* improved documentation of plot method (closes :issue:`169`).

* improved auto-completion in ipython interactive consoles for both LArray and Session objects. LArray objects can now
  complete keys within [].

    >>> a = ndrange('sex=Male,Female')
    >>> a
    sex | Male | Female
        |    0 |      1
    >>> a['Fe<tab>`

  will autocomplete to `a['Female`. Sessions will now auto-complete both attributes (using `session.`) and keys
  (using `session[`).

    >>> s = Session({'a_nice_test_array': ndtest(10)})
    >>> s.a_<tab>

  will autocomplete to `s.a_nice_test_array` and `s['a_<tab>` will be completed to `s['a_nice_test_array`

* made warning messages for division by 0 and invalid values (usually caused by 0 / 0) point to the user code line,
  instead of the corresponding line in the larray module.

* preserve order of arrays in a session when saving to/loading from an .xlsx file.

* when creating a session from a directory containing CSV files, the directory may now contain other (non-CSV) files.

* several calls to open_excel from within the same program/script will now reuses a single global Excel instance.
  This makes Excel I/O much faster without having to create an instance manually using xlwings.App, and still without
  risking interfering with other instances of Excel opened manually (closes :issue:`245`).

* improved error message when trying to copy a sheet from one instance of Excel to another (closes :issue:`231`).


Fixes
-----

* fixed keyword arguments such as `out`, `ddof`, ... for aggregation functions (closes :issue:`189`).

* fixed percentile(_by) with multiple percentiles values, i.e. when argument `q` is a list/tuple (closes :issue:`192`).

* fixed group aggregates on integer arrays for median, percentile, var and std (closes :issue:`193`).

* fixed group sum over boolean arrays (closes :issue:`194`).

* fixed set_labels when inplace=True.

* fixed array creation functions not raising an exception when called with wrong syntax func(axis1, axis2, ...)
  instead of func([axis1, axis2, ...]) (closes :issue:`203`).

* fixed position of added sheets in excel workbook: new sheets are appended instead of prepended (closes :issue:`229`).

* fixed Workbook behavior in case of new workbook: the first added sheet replaces the default sheet `Sheet1`
  (closes :issue:`230`).

* fixed name of Workbook sheets created by copying another sheet (closes :issue:`244`).

    >>> wb = open_excel()
    >>> wb['name_of_new_sheet'] = wb['name_of_sheet_to_copy']

* fixed with_axes warning to refer to set_axes instead of replace_axes.

* fixed displayed title in viewer: shows path to file associated with current session + current array info +
  extra info (closes :issue:`181`)
