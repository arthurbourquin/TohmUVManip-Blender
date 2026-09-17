### Ancienne structure

`local/`
    `work/`
        `TohmUVManip/`
            `TohmUVManip.py` avec tout dedans
`local/`
    `BlenderAddons/`
        `TohmUVManip.py` symlink de fichier `local/work/TohmUVManip/TohmUVManip.py`


### Nouvelle structure

`local/`
    `work/`
        `TohmUVManip/` repo_local
            `.gitignore`
            `README.md`
            `TohmUVManip/`
                `__init__.py` importe operator et ui
                `ui.py`
                `operators.py` importe UvGraph
                `UvGraph/` 
                    `__init__.py` importe seulement UvGraph
                    `uv_vert.py`
                    `uv_connected_graph.py`
                    `uv_graph.py` importe UvVert UvConnectedGraphs
toutes les petites classes genre UvVertDict ou UvCo sont remplacées par list, tuple, set, et dict

`local/`
    `BlenderAddons/`
        `TohmUVManip/` symlink de dossier `local/work/TohmUVManip/TohmUVManip`
`github/`
    `TohmUVManip-Blender/` repo distant

