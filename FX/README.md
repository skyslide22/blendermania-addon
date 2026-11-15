# tm_fx – schema-driven TM2020 particle/VFX editor for Blender

Drop the `tm_fx/` folder into your add-on (or install it as its own add-on), then call
`tm_fx.register()` / `tm_fx.unregister()` from your `register()`. UI appears in
**Properties ▸ Scene ▸ TM Item FX**. Tested on Blender 5.0.1 (uses only long-stable API).

```python
from tm_fx import api
doc = api.export_fx(scene)   # dict to embed in your item JSON (None if FX is off)
api.import_fx(scene, doc)    # load a dict, e.g. dumped from a working item
```

## How it works
`tools/gen_schema.py` reads GBX.NET's `.chunkl` files and writes `tm_fx/schema/base/*.json`
(TM2020 only, version-resolved). Blender properties, UI, import/export and the template diff
are all generated from that schema. Hand-written knowledge lives in `tm_fx/schema/overlay/*.json`
(labels, ranges, grouping, `status`, `choices`, `visible_if`) and survives regeneration.

    python tools/gen_schema.py --gbxnet /path/to/gbx-net     # regenerate base
    python tests/test_blender.py                             # needs `pip install bpy` (py3.11)

Field `status`: `verified` (confirmed in game – set it yourself) · `named` (GBX.NET gives a name) ·
`guess` · `unknown` (`U01…`). The **Show** filter hides unknown fields by default.

## Workflow
1. Dump a working effect to JSON (format below) and **Import ▸ use as template** – changed values
   get a reset button; unknown data is carried through untouched (`extra`).
2. Edit known fields, toggle chunks, add/duplicate emitters, sub-models, curves.
3. Probe unknowns: change one `Unknown` field, test in game, then record it in the overlay.

## Wire format (what your converter reads) – see `tm_fx/codec.py`
Node: `{"$class", "props": {NamedMember: v}, "chunks": {"0x090C6000": {"Version": 6, "U01": v}}, "extra"?}`  
Struct: `{"$struct": "CPlugVFXFile.Parameter", "props": {Member: v}}`. Child nodes nest in place of the
member value (`null` = no node). Named → `node.<Name>`; `Unnn` → `GetChunk<Chunk…>().Unn`
(numbering verified against GBX.NET's generated code for all 42 particle/VFX chunks).
Enums as ints, vectors as arrays, blobs as hex, refs as path strings, curves as
`{"version":3,"flags":int,"points":[[t,v]…]}` (flag bits: 1 step, 2 smooth, 0x10 hermite, 0x20 tangent).

## Known limits
* The "GPU emitter" button builds a *skeleton* from schema defaults (all chunks on) – load a template for real values.
* `Parameter.Type` labels, default chunk set and which chunks the game requires are inferred, not tested.
* `GxLightBall`, legacy curve refs and 64-bit ints are opaque (omitted). `CPlugFxSystem` is not exposed (vehicle-only).
* Curves are edited as a key list (no graph widget yet).

## Preview (approximate, `tm_fx/preview.py`)
**Scene ▸ TM Item FX ▸ Preview** drives a hidden native particle system (collection `TMFX_Preview`) from
the GPU model under the selected node. Press *Update* after edits, *Clear* to remove it.

| GBX field | Blender |
|---|---|
| `LifeMax` (s), `LifeVar01` | lifetime (frames), lifetime randomness |
| `SizeMax`, `SizeVar01` | particle size, size randomness |
| `Weight` x *Gravity scale* | gravity weight (Weight's meaning is a guess; default scale 0) |

Rate, speed and spawn shape are **preview-only** (the spawn fields are still unknown) and never exported.
Not mapped: size-over-life, texture/atlas, intensity, hue, colour. Particles are instanced blobs, not billboards.
