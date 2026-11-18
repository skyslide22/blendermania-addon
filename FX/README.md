# FX – particle effects for TM2020 items

Schema-driven editor for the particle effects of an item. An **empty** marked as *Particle FX*
(object panel ▸ `Particle FX` toggle, name infix `_particleFX_`) places one effect; it is edited in
**Blendermania ▸ ManipulationsV2 ▸ Particle FX** and written to the item config on export:

```json
"ParticleFx": [
  { "Name": "Smoke_particleFX_", "Variant": null,
    "Fx": { "format": "tm-fx/1", "vfx": { "$class": "CPlugFxSystem", "props": {}, "chunks": {} } } }
],
"Assets": [ { "Id": "SmokeAtlas", "Path": ".../SmokeAtlas.Texture.Gbx", "Type": "Bitmap" } ]
```

TM_GenericMapping (`FbxParticleFxConverter` / `ParticleFxConverter`) converts `Fx` into a
`CPlugFxSystem` and places it at the fbx node called `Name` (world transform of the empty).
Effects inside a variant collection get `Variant`.

## Schema (generated, never hand-authored)
`tools/gen_schema.py` reads GBX.NET's `.chunkl` files and writes `schema/base/*.json` (TM2020,
version-resolved) for every class reachable from the root `CPlugFxSystem`. Blender properties, UI,
import/export, validation and the template diff are all generated from it.

    python FX/tools/gen_schema.py --gbxnet /path/to/gbx-net

`schema/overlay/*.json` only adds what GBX.NET does not know (labels, ranges, `status`, `choices`,
`visible_if`) and survives regeneration. Field `status`: `verified` · `named` · `guess` · `unknown`
(`U01…`); the **Show** filter hides unknown fields by default.

## Assets
`CPlugBitmap` members of nodes (e.g. `CPlugParticleGpuModel.Bitmap`, `BitmapOverLife`) are pointers
to **Bitmap assets** of the asset library, exactly like the veget tree propagation bitmaps: on export
the asset is added to `ItemConfig.Assets` and the member holds its id. The converter references the
`.Texture.Gbx` as a file instead of embedding it.

Not assets (by design, for now): material/shader/mesh/sound references and anonymous (`Uxx`) bitmap
members of chunks – they are plain `.Gbx` path strings, empty by default.

## Workflow
1. Toggle *Particle FX* on an empty: the effect starts with a group root node (`Type 0`).
2. *Structure*: add effect nodes (`Emitter` adds Type 4 ▸ emitter ▸ sub-model ▸ GPU spawn + GPU model
   with schema defaults), select a row and edit it in *Selected node*.
3. Or **Import GBX** a game effect, e.g. `GameData/Stadium/MotionParticleEmitterModel/Fogger8M.ParticleModel.Gbx`
   (emitter, wrapped in an fx system) or a `*.FxSys.Gbx`, then pick your bitmap asset. The dotnet command
   `convert-fx-to-json` (TM_GenericMapping `ParticleFxJsonWriter`) writes it as `tm-fx/1`; named bitmaps keep their
   path (matched to an asset by name), every other reference is left empty. **Import JSON** loads a `tm-fx/1` file.
   *Use as template* highlights changes; unknown data is carried through as `extra`.
4. Export the item: effects with errors (root without type, non-bitmap asset) skip the item with a report.

## Wire format (`codec.py`)
Node: `{"$class", "props": {NamedMember: v}, "chunks": {"0x0915C000": {"Version": 2, "U01": v}}, "extra"?}`  
Struct: `{"$struct": "CPlugFxSystem.EffectNode", "props": {Member: v}}`. Child nodes/structs nest in place
of the member value (`null` = no node). Named → `node.<Name>`; `Unn` → `GetChunk<Chunk…>().Unn`.
Enums as ints, vectors as arrays, blobs as hex, refs as strings (asset id or .Gbx path), curves as
`{"version":3,"flags":int,"points":[[t,v]…]}` (flag bits: 1 step, 2 smooth, 0x10 hermite, 0x20 tangent).
Only fields whose GBX.NET condition holds are written (e.g. `EffectNode.Emitter` only for `Type == 4`).

## Known limits
* `EffectNode.Type` labels come from the members GBX.NET reads per type.
* Emitter node expressions (`EffectNode.U02`-`U15`, e.g. `float3(0,1,0)`, `1`, `0.5`) default to the values all Nadeo
  fx systems use; empty expressions make the effect invisible in game. `InputClassId`/`OutputClassId` default to
  0xFFFFFFFF like Nadeo's (uint32 fields are stored as signed bit pattern in Blender).
* `GxLightBall`, legacy curve refs and 64-bit ints are opaque (omitted).
* Particle empties inside instanced collections are not exported.

## Preview (approximate, `preview.py`)
*Particle FX ▸ Preview* (header checkbox) draws a viewport **overlay**: nothing is added to the scene,
nothing can be exported. Particles are simulated from the timeline time (scrub or press Play) and
drawn as camera facing sprites, for every GPU model of the effect, for the active or all fx empties.

| GBX field (GPU model) | Preview |
|---|---|
| `LifeMax`, `LifeVar01` | lifetime (s) and its randomness |
| `SizeMax`, `SizeVar01`, `SizeEndScale` | start size, randomness, linear size change over life |
| `Weight` x *Gravity scale* | gravity (Weight's meaning is a guess; scale 0 by default) |
| `Intensity` | sprite brightness |
| `IntensityFadeIn/Out`, `IntensityPower`, `IntensityVariation` | fade in/out as fraction of life, fade-out curve exponent, per particle brightness (*Fade (guess)*) |
| Effect node `U09` (forward axis) | emission direction in Trackmania axes (`float3(0,0,-1)` = Blender +Y of the empty) |
| GPU spawn `U04`, `U11`, `U12` | rate (1/s), speed (m/s), speed variation: found in game tests (*From GPU spawn*) |
| `Bitmap`, `TextureAtlasDimX/Y` | bitmap asset image; atlas cell over life / random / first (game behaviour unknown) |

Rate, speed, spread and spawn shape are **preview-only** (the spawn fields are unknown) and never exported.
Not shown: effect node logic (conditions, sub systems, variables), `BitmapOverLife`, colour/hue, rotation,
blend modes, mesh/splash particles, lights. Files from the old particle-system preview get a cleanup button.

### Veget tree propagation
The same overlay animates the falling leaves of tree models (*Tree Model collection ▸ Show Propagation*,
shown when *Enable Propagation* is on), for every visible tree model of the scene: leaves spawn in a horizontal
disc of *Spawn Radius* around the *Emission Positions* (relative to the tree model's first mesh, location and rotation),
*Leaves Per Second* in total, fall inside the *Cone Half Angle* around straight down, *Leaf Size*,
*BaseColor* bitmap with a random *Atlas Grid* cell, and disappear at the tree mesh's height.
Rate factor, fall speed, leaf life and spin are preview-only (the game shows fewer leaves than *Leaves Per Second* suggests; defaults matched by eye: rate factor 0.1, leaf life 8 s) (no tree setting is known for how long leaves live).
Not used: *Ground Point Count* (meaning unknown) and the normal bitmap. *Scale Variation* is the tree's random size
(`ScaleVar01`), not a propagation setting.
