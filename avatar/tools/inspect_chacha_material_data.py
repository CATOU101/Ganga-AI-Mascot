import json
import os

import bpy


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILES = [
    os.path.join(ROOT, "01_Reference", "Chacha_Mixamo.fbx"),
    os.path.join(ROOT, "02_Character", "character.fbx"),
    os.path.join(ROOT, "02_Character", "Chacha_v01_Base.blend.blend"),
]
OUT = os.path.join(ROOT, "08_Final", "Chacha_Material_Inspection.json")


def material_summary(mat):
    item = {
        "name": mat.name,
        "diffuse_color": list(mat.diffuse_color),
        "use_nodes": mat.use_nodes,
        "nodes": [],
    }
    if mat.use_nodes:
        for n in mat.node_tree.nodes:
            entry = {"name": n.name, "type": n.type}
            if n.type == "BSDF_PRINCIPLED":
                entry["base_color"] = list(n.inputs["Base Color"].default_value)
                entry["roughness"] = n.inputs["Roughness"].default_value
            if n.type == "TEX_IMAGE" and n.image:
                entry["image"] = {"name": n.image.name, "filepath": bpy.path.abspath(n.image.filepath), "size": list(n.image.size)}
            item["nodes"].append(entry)
    return item


def inspect_file(path):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    if path.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    else:
        bpy.ops.wm.open_mainfile(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    images = []
    for img in bpy.data.images:
        if img.name not in {"Render Result", "Viewer Node"}:
            images.append({"name": img.name, "filepath": bpy.path.abspath(img.filepath), "size": list(img.size), "packed": bool(img.packed_file)})
    return {
        "path": path,
        "meshes": [
            {
                "name": o.name,
                "vertices": len(o.data.vertices),
                "polygons": len(o.data.polygons),
                "materials": [slot.material.name if slot.material else None for slot in o.material_slots],
                "color_attributes": [attr.name for attr in getattr(o.data, "color_attributes", [])],
                "uv_layers": [uv.name for uv in o.data.uv_layers],
            }
            for o in meshes
        ],
        "materials": [material_summary(m) for m in bpy.data.materials],
        "images": images,
    }


def main():
    result = []
    for path in FILES:
        if os.path.exists(path):
            result.append(inspect_file(path))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
