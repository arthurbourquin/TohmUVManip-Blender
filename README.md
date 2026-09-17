# TohmUVManip-Blender

Work in progress...

## Basics

- Allow uv points manipulations based on theirs **coordinates** and **connections**
    - **coordinates**: severals vertex/loop at the same location in UV Editor are treated as a single point
    - **connections**: operations are based on current selection, specifically on a selection of edges in the UV Editor forming a path


## In Depth

This Add-on rely mostyl on an included graph class named `UvGraph` respecting the common graph theory, allowing to get information about the structure of the selection.

Works in `UV Sync Selection` mode but this will restrict possibiliies.



