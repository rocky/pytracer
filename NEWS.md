2.0.0 - 10-14-24
================

* Allow filtering by module. This makes use in ``trepan3k`` and other places that want to use simpler and more powerful.
* Modernize for 3.13 (the last release was for Python 2.7!) - redo tests in `pytest`

API incompatibility:
  `is_included` (in a trace filter) is now called `is_excluded` (with respect to the code being debugged)

0.3.1 - 03-06-13
================

* Packaging missed a couple of key files

0.3.0 - 02-13-13
================

* Make trepan3k compatible

0.2.5 - 11-01-10
================

* Don't depend on import_relative in packaging since the rest of the  package doesn't need it!

0.2.4 - 10-27-10
================

* Improve packaging (not - see above).

0.2.3 - 12-25-09
================

* add_hook bug fixes boolean option 'front' changed to integer option 'position'

0.2.2 - 03-08-09 Ron Frankel - 1 release
========================================

* Add `EVENT2SHORT`: event name to a short string used in `pydbgr`. For example, 'call' is '->'.
* Leave a mark in the frame so clients like pydbgr can know to omit
  listing this kind of frame (for in thread debugging)
* Add a debug flag for showing all events that come through.
* Make GPL v3

Above changes in are support of `pydbgr`

0.2.0 - 12-25-08
================

* Initial googlecode release
