import json
import os

import bpy


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FBX = os.path.join(ROOT, "01_Reference", "Chacha_Mixamo.fbx")
OUT = os.path.join(ROOT, "08_Final", "Chacha_Vertex_Profile.json")


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.ops.import_scene.fbx(filepath=FBX, automatic_bone_orientation=False)
    obj = bpy.data.objects.get("Chacha_Mixamo") or next(o for o in bpy.context.scene.objects if o.type == "MESH")
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    zmin = min(p.z for p in pts)
    zmax = max(p.z for p in pts)
    bins = []
    for i in range(20):
        a = zmin + (zmax - zmin) * i / 20
        b = zmin + (zmax - zmin) * (i + 1) / 20
        slice_pts = [p for p in pts if a <= p.z < b]
        if not slice_pts:
            continue
        bins.append(
            {
                "z_range": [a, b],
                "count": len(slice_pts),
                "x_min": min(p.x for p in slice_pts),
                "x_max": max(p.x for p in slice_pts),
                "y_min": min(p.y for p in slice_pts),
                "y_max": max(p.y for p in slice_pts),
                "x_avg": sum(p.x for p in slice_pts) / len(slice_pts),
                "y_avg": sum(p.y for p in slice_pts) / len(slice_pts),
            }
        )
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(bins, f, indent=2)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
