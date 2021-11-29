.. nice documentation master file, created by
   sphinx-quickstart on Mon May 17 17:36:17 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

NICE documentation
==================

The Noise Interactive Catalogue Explorer (NICE) is a web application
dedicated to the noise characterization in gravitational waves
interferometers. In the current version, it contains tools for studying 
rapid non-gaussian noises (glitches) present in Virgo detector.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   installation
   configuration
   investigationflow

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

NICE components
---------------

3 main components:

1. Glitch Database (GlitchDB);
2. Interactive Plot Window (IPW);
3. Single Glitch Analysis Window (SGAW);

NICE is currently used for the Virgo glitches morphology and origin 
investigation. The application leads from the selection of glitches with 
certain properties (GlitchDB) to the identification of the single 
transient noise (SGAW), passing through the glitches distrubution around an 
gravitational wave candidate (IPW). In this documentation are shown the 
NICE utilities applied to real unclassified and simulated glitches families.
