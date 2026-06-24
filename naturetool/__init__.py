bl_info = {
    "name": "Nature Tool",
    "author": "naturetool contributors",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Nature",
    "description": "Tools for assembling natural elements from artist-made meshes.",
    "category": "Object",
}

from . import operators
from . import panels
from . import properties

modules = (
    properties,
    operators,
    panels,
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
