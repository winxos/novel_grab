AISTLAB novel grab
==================

    novel grab crawler module using python3 and lxml

    multiprocesssing with multithread version

    winxos, AISTLAB Since 2017-02-19

INSTALL:
--------

``pip3 install aistlab_novel_grab``

1. USAGE:
---------

RUN COMMAND IN CONSOLE:

``novel_grab http://the_url_of_novel_chapters_page``

EXAMPLE:

``novel_grab http://book.zongheng.com/showchapter/654086.html``

    **SUPPORTED SITES:** \* http://book.zongheng.com \*
    http://www.aoyuge.com \* http://www.quanshu.net

2. USAGE AS PYTHON MODULE:
--------------------------

.. code:: python

        from novel_grab.novel_grab import Downloader
        d = Downloader()
        print(d.get_info())
        if d.set_url('http://book.zongheng.com/showchapter/221579.html'):
            d.start()

    **TIPS** \* When d = Downloader(), d.get\_info() can get supported
    sites info. \* Once d.set\_url(url) will return the url is valid or
    not. \* Of course you can use d.get\_info() to access the state of d
    at any time. \* While finished, will create :math:`novel_name`.zip
    file in your current path, default zip method using
    zipfile.ZIP\_DEFLATED

**Just for educational purpose, take care of yourself.**
