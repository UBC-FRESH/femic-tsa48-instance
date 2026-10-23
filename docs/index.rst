FEMIC Full TSA 48 Instance
==========================

Standalone FEMIC and ws4 model instance for the full North Island TSA 48 area
of interest. FEMIC rebuilds the public model inputs and the Patchworks
interchange package; ws4 compiles the full model, runs the AAC benchmark, and
serves it in its own web UI.

**Runtime lane:** ws4 is the primary runtime. Patchworks is reference-only.

**Related instance:** the independent NICC + K3Z dataset lives in
`UBC-FRESH/femic-northisland-instance <https://github.com/UBC-FRESH/femic-northisland-instance>`_.
The two are deliberately related but can be used separately; see
``notes/reference/related-instances.md``.

This site is the RTFM surface for the project. Agents read the relevant page
before they act, and cite it in their reports. Start with the repository's
``AGENTS.md`` and ``ROADMAP.md``.

.. toctree::
   :maxdepth: 2
   :caption: Guides

   aoi
   model-build
   web-ui

.. toctree::
   :maxdepth: 2
   :caption: API

   api/index
