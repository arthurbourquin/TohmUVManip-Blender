## structure

`local/`
    `work/`
        `TohmUVManip-Blender/` repo_local
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
        `TohmUVManip/` symlink de dossier `local/work/TohmUVManip-Blender/TohmUVManip`
`github/`
    `TohmUVManip-Blender/` repo distant


symlink mac:
ln -s /Volumes/Macintosh\ HD/Users/arthurbourquin/LOCAL/Guiteub/TohmUVManip-Blender/TohmUVManip /Volumes/Macintosh\ HD/Users/arthurbourquin/Library/Application\ Support/Blender/5.2/scripts/addons/TohmUVManip

