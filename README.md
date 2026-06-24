# Nature Tool

Blender 4.5 add-on for assembling natural elements from artist-made meshes.

The first generator creates a bush around the 3D cursor by distributing selected
mesh objects into a new collection. The package is structured so future
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
