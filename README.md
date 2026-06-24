# Nature Tool

Blender 4.5 add-on for assembling natural elements from artist-made meshes.

The first generator creates an editable bush controller around the 3D cursor.
Selected mesh objects are stored as source geometry, and generated instances are
rebuilt from the controller settings. The package is structured so future
generators can be added without putting all logic in Blender UI classes.

## Development Install

Run this from the repository root in PowerShell:

```powershell
.\tools\install_dev_link.ps1
```

This creates a junction from Blender's add-on folder to the local package:

```text
%APPDATA%\Blender Foundation\Blender\4.5\scripts\addons\naturetool
  -> D:\github\naturetool\naturetool
```

Then open Blender 4.5 and enable the add-on:

```text
Edit > Preferences > Add-ons > Nature Tool
```

Use the panel here:

```text
3D Viewport > Sidebar > Nature > Nature Tool
```

Place the 3D cursor where the bush should be created, select one or more mesh
objects, and press `Create Bush`.

Source meshes should use local `-Y` as the branch direction and local `+Z` as
up. Generated instances rotate so their local `-Y` points away from the bush
controller.

The add-on selects the new `Bush Controller` empty after creation. Select that
controller later to edit the bush:

- Move, rotate, or scale the empty to transform the whole bush.
- Change instances, radius, height, or seed in the Nature panel.
- Press `Update Bush`, or enable `Live Update` for immediate rebuilds.
- Select mesh sources along with the active controller and press
  `Set Sources From Selection` to replace the source list.

## Project Layout

```text
naturetool/
  __init__.py              Blender add-on entry point
  blender_manifest.toml    Blender extension manifest
  properties.py            Scene-level settings
  operators/               Blender operators
  panels/                  Viewport UI panels
  generators/              Pure generation logic
```

## Smoke Test

Run this from the repository root:

```powershell
& "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" `
  --background `
  --factory-startup `
  --python .\tools\smoke_test_interactive_bush.py
```
