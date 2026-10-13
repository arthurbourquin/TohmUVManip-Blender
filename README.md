# TohmUVManip-Blender

Work in progress...

## Basics

- Allow uv points manipulations based on theirs **coordinates** and **connections**
    - **coordinates**: severals vertex/loop at the same location in UV Editor are treated as a single point
    - **connections**: operations are based on current selection, specifically on a selection of edges in the UV Editor forming a path


## In Depth

This Add-on rely mostyl on an included graph class named `UvGraph` respecting the common graph theory, allowing to get information about the structure of the selection.

`UvGraph` is a direct representation on the current UV selection.
It handles all four `vert`, `edge`, `face`, `loop` objects in a more intuitive way and easyer to maniulate, especially regarding cases like:
- overlapping UV-Editor-vertices in a single 3D-View-vertex
- overlapping UV-Editor-edges in a single 3D-View-edges
- overlapping overlapping UV-Editor-vertices that are separated 3D-View-vertices
- overlapping overlapping UV-Editor-edges that are separated 3D-View-edges

Due to this architecture, `UV Sync Selection` (that sometines messes a little up distinction of selected elements) may not be haldeled properly. Depending the version, the addon may turn off the mode.