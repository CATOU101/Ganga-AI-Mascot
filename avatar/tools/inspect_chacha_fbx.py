import json
import os
import sys

import bpy


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FBX = os.path.join(ROOT, "01_Reference", "Chacha_Mixamo.fbx")
OUT = os.path.join(ROOT, "08_Final", "Chacha_FBX_Inspection.json")


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.ops.import_scene.fbx(filepath=FBX, automatic_bone_orientation=False)

    data = {
        "objects": [],
        "armatures": [],
        "materials": [],
        "images": [],
        "actions": [],
    }

    for obj in bpy.context.scene.objects:
        entry = {
            "name": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "dimensions": list(obj.dimensions),
            "location": list(obj.location),
            "modifiers": [{"name": m.name, "type": m.type} for m in obj.modifiers],
            "vertex_group_count": len(obj.vertex_groups) if hasattr(obj, "vertex_groups") else 0,
        }
        if obj.type == "MESH":
            entry["materials"] = [slot.material.name if slot.material else None for slot in obj.material_slots]
        data["objects"].append(entry)

    for arm_obj in [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]:
        arm_obj.data.pose_position = "POSE"
        bones = []
        for pb in arm_obj.pose.bones:
            bones.append(
                {
                    "name": pb.name,
                    "parent": pb.parent.name if pb.parent else None,
                    "head": list(arm_obj.matrix_world @ pb.head),
                    "tail": list(arm_obj.matrix_world @ pb.tail),
                }
            )
        data["armatures"].append({"name": arm_obj.name, "bones": bones})

    for mat in bpy.data.materials:
        data["materials"].append({"name": mat.name, "use_nodes": mat.use_nodes})
    for img in bpy.data.images:
        data["images"].append({"name": img.name, "filepath": bpy.path.abspath(img.filepath)})
    for action in bpy.data.actions:
        data["actions"].append({"name": action.name, "frame_range": list(action.frame_range)})

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
