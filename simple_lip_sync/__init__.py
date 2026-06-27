"""Simple Lip Sync Blender add-on entry point."""

bl_info = {
    "name": "Simple Lip Sync",
    "author": "Half-Bottled Reverie, Simple Lip Sync contributors",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Simple Lip Sync",
    "description": "Generate MMD-style lip sync shape-key animation from audio.",
    "category": "Animation",
}


def register():
    """Register the add-on."""
    from .blender import i18n
    from .blender import ui

    i18n.register()
    ui.register()


def unregister():
    """Unregister the add-on."""
    from .blender import i18n
    from .blender import ui

    ui.unregister()
    i18n.unregister()
