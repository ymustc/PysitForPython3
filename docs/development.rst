.. _dev_guide:

*****************
Developer's Guide
*****************

This document describes the preferred method for developing the core PySIT
package.

.. note::

    This document is lacking in some areas.  If anything is confusing, please
    do not hesitate to contact the developers for clarification.

    A very good resource on developing is the `Astropy Developer Documentation
    <http://docs.astropy.org/en/stable/index.html#developer-documentation>`_,
    upon which future versions of this documentation will be based. Many of
    their specifications are not applicable for this project, but many more
    are. Studying their guide is a very good way to get started.  Note that
    many of their `git` specific directives have Mercurial (`hg`) equivalents.


DVCS and Hosting
================

PySIT uses Mercurial (`hg`) for version control and `BitBucket.org
<http://www.bitbucket.org>`_ for code and project hosting.  You will need to
install the appropriate version of Mercurial for your platform.  If you are
new to distributed version control (DVCS) or Mercurial,
`<http://www.hginit.com>`_ is a good place to get started.

.. note::

    If you are an academic, be sure to use your academic e-mail to register
    with BitBucket.  The benefits are worth it.

.. note::

    For Windows and Mac OSX users, `Atlassian's SourceTree
    <http://www.sourcetreeapp.com/>`_ is a nice all-in-one Mercurial and Git
    tool.  On Windows, we've also had success with `TortoiseHg
    <http://tortoisehg.bitbucket.org/>`_.

PySIT's `documentation <http://example.com>`_ is hosted by ReadTheDocs.


Forking PySIT
=============

PySIT development will take place in your own "fork" of the `main PySIT
repository <https://bitbucket.org/pysit/pysit>`_.  A fork is a "clone" of the
repository and is hosted on your personal BitBucket account.  You will use
this fork for developing new PySIT features.  Your changes will migrate to the
core repository (for review and merging) by requesting that the main
repository "pull" in your changes.  This is known as a *pull request* and is
facilitated through the BitBucket website.

After creating your fork, you will need to create a local clone:

.. code::

    hg clone https://<username>@bitbucket.org/<username>/pysit <target_dir>

Your development will occur in your local clone.

Development Workflow
====================

A rough sketch of the workflow for adding new features to PySIT is described
below.  Please use this for adding new general features and methods from the
literature.  If you are developing new research and are not sure if it belongs
in PySIT, please ask or use a PySIT Extension package.

.. note::

    We will follow the branching strategy specified by `A successful Git
    branching model
    <http://nvie.com/posts/a-successful-git-branching-model/>`_ (just replace
    the relevant `git` commands with their `hg` equivalent).  This strategy is
    implemented with the `hg-flow` Mercurial extension and is integrated with
    SourceTree.

.. note::

    We will refer to the `main PySIT repository
    <https://bitbucket.org/pysit/pysit>`_ as the `upstream` repository.  You
    can add this to, add the following line to your `.hg/hgrc` file:

    .. code::

        upstream = https://<username>@bitbucket.org/pysit/pysit

    and substitute your username.

Roughly, the procedure for adding a new feature or fixing a bug is:

1) In your local clone of *your* fork of the main PySIT repository, create a
   branch for the feature or bug.  If the bug has been `reported
   <https://bitbucket.org/pysit/pysit/issues?status=new&status=open>`_,
   reference the issue number in the branch name.

2) Develop your feature or fix the bug.  In this branch, avoid any other
   changes that are not related.

3) When you think your change is complete, or  you have a question and want to
   initiate code review, pull the latest version of the `develop` branch in 
   main PySIT repository into your local branch and resolve any merge 
   conflicts.

4) Push your changes to your fork on BitBucket.

5) From BitBucket, issue a "pull request" from your feature branch to the
   `develop` branch of the main PySIT repository.

6) Comments may be given.  Address them locally and push them to your
   repository on BitBucket.  The pull request will update automatically.

7) Once the pull request is accepted and merged, you may close your branch.

8) Pull the upstream `develop` branch into your local `develop` branch.

.. note::

    This is roughly the standard procedure used in most DVCS hosted projects.
    Improvements to the process are always welcome.

Coding Standards
================

* We follow the Python `PEP8 <http://www.python.org/dev/peps/pep-0008/>`_ style
  guide.

    .. note::

        Older PySIT code still uses tabs for indentation of Python code
        blocks.  These are being phased out.  If you modify such a file, be
        careful to not mix conventions.

* Class and function docstrings should follow the `numpydoc conventions
  <https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt>`_.

* Test coverage is sparse.  Try to include unit tests on new code and on bug
  fixes to help catch regression bugs.  Improvement of test coverage is a major
  focus going forward.

* Pull requests **must** include updates to the documentation.  Run a spell
  checker.