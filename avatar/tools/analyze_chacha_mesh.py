import json
import os
from collections import defaultdict, deque

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FBX = os.path.join(ROOT, "01_Reference", "Chacha_Mixamo.fbx")
OUT = os.path.join(ROOT, "08_Final", "Chacha_Mesh_Components.json")


def components_for_mesh(obj):
    mesh = obj.data
    adjacency = defaultdict(set)
    for e in mesh.edges:
        a, b = e.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)

    seen = set()
    comps = []
    for i in range(len(mesh.vertices)):
        if i in seen:
            continue
        q = deque([i])
        seen.add(i)
        ids = []
        while q:
            cur = q.popleft()
            ids.append(cur)
            for nxt in adjacency[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        pts = [obj.matrix_world @ mesh.vertices[idx].co for idx in ids]
        mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        comps.append(
            {
                "vertex_count": len(ids),
                "min": list(mn),
                "max": list(mx),
                "center": list((mn + mx) * 0.5),
                "size": list(mx - mn),
            }
        )
    comps.sort(key=lambda c: c["vertex_count"], reverse=True)
    return comps


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.ops.import_scene.fbx(filepath=FBX, automatic_bone_orientation=False)
    result = {}
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            result[obj.name] = {
                "vertex_count": len(obj.data.vertices),
                "edge_count": len(obj.data.edges),
                "poly_count": len(obj.data.polygons),
                "bounds": {
                    "min": list(obj.matrix_world @ Vector((min(v.co.x for v in obj.data.vertices), min(v.co.y for v in obj.data.vertices), min(v.co.z for v in obj.data.vertices)))),
                    "max": list(obj.matrix_world @ Vector((max(v.co.x for v in obj.data.vertices), max(v.co.y for v in obj.data.vertices), max(v.co.z for v in obj.data.vertices)))),
                },
                "components": components_for_mesh(obj)[:80],
            }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
