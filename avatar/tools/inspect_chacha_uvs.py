import json
import os

import bpy


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILES = [
    os.path.join(ROOT, "01_Reference", "Chacha_Mixamo.fbx"),
    os.path.join(ROOT, "02_Character", "character.fbx"),
]
OUT = os.path.join(ROOT, "08_Final", "Chacha_UV_Inspection.json")


def inspect(path):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    result = {"path": path, "meshes": []}
    for obj in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        layer = obj.data.uv_layers.active
        if not layer:
            continue
        us = [uv.uv.x for uv in layer.data]
        vs = [uv.uv.y for uv in layer.data]
        tiles = {}
        for uv in layer.data:
            key = f"{int(uv.uv.x)}_{int(uv.uv.y)}"
            tiles[key] = tiles.get(key, 0) + 1
        result["meshes"].append(
            {
                "name": obj.name,
                "verts": len(obj.data.vertices),
                "polys": len(obj.data.polygons),
                "uv_min": [min(us), min(vs)],
                "uv_max": [max(us), max(vs)],
                "tiles": tiles,
            }
        )
    return result


def main():
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump([inspect(path) for path in FILES if os.path.exists(path)], f, indent=2)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
