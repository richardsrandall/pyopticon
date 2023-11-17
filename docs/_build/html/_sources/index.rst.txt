.. PyOpticon documentation master file, created by
   sphinx-quickstart on Fri Sep  8 12:22:35 2023.

   The best Sphinx cheat sheet is here:
   https://sphinx-rtd-tutorial.readthedocs.io/en/latest/build-the-docs.html#building-our-documentation

Welcome to PyOpticon's documentation
=======================================

This package creates graphical user interfaces that control, automate, and log data from physical devices via serial connections. 
It was originally developed for use in a laboratory setting with devices like valves, mass flow controllers, and spectrometers, though it will work 
well with many other devices that can communicate with a serial connection. 
Our goal is to enable graduate students and 
other researchers with basic Python knowledge to quickly equip experimental setups with data acquisition and 
automated control, allowing higher-quality and higher-throughput experimentation. 
See the Gallery tab for some examples.

The graphical user interfaces are called *Dashboards* and consist of many 
elements called *Widgets* that represent a physical device or a group of functions. Existing dashboards can be operated like desktop applications, without any coding knowledge, 
once they are created. Writing automation scripts, configuring new dashboards from existing widgets, and defining new widgets require as little coding as we 
could manage.

The project can be installed using pip from PyPI_ and its source code is available on Github_. While it is in early development, 
it may be best to download and use the source from Github, since the author can then quickly send you patches for any use-case-specific 
bugs that become apparent. See the Overview page.

.. _PyPI: https://pypi.org/project/pyopticon/
.. _Github: https://github.com/richardsrandall/pyopticon

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   gallery
   capabilities
   tutorial_1
   tutorial_2
   tutorial_3
   tutorial_4
   documentation
   license



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
