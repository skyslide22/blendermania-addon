import bpy
from bpy.props import *

from ..properties.PlacementPatchProperties import CompatiblePatchGroupProperty, PlacementPatchProperties
from ..properties.Functions import getSimpleGridParams


class PivotsProperties(bpy.types.PropertyGroup):
    """trackmania properties generated for pivots (item xml)"""
    FV_position   : FloatVectorProperty(name="Pivot Position", size=3, subtype='XYZ', default=(0.0, 0.0, 0.0), step=100)
    FV_rotation   : FloatVectorProperty(name="Pivot Rotation", size=3, subtype='EULER', default=(0.0, 0.0, 0.0), step=100)

    # NU_pivotX   : FloatProperty(name="X", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)
    # NU_pivotY   : FloatProperty(name="Y", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)
    # NU_pivotZ   : FloatProperty(name="Z", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)

    # NU_pivotRotX   : FloatProperty(name="X", default=0.0, min=0, max=360, soft_min=0, soft_max=360, step=10)
    # NU_pivotRotY   : FloatProperty(name="Y", default=0.0, min=0, max=360, soft_min=0, soft_max=360, step=10)
    # NU_pivotRotZ   : FloatProperty(name="Z", default=0.0, min=0, max=360, soft_min=0, soft_max=360, step=10)


def _set_CB_alignToWorldDir_when_set_interior(self, context):
    if self.CB_alignToInterior is True:
        self.CB_alignToWorldDir = False

def _set_CB_alignToInterior_when_set_world(self, context):
    if self.CB_alignToWorldDir is True:
        self.CB_alignToInterior = False

def _updateGridAndLevi(self, context) -> None:
    place_xy = self.NU_gridAndLeviX
    place_z  = self.NU_gridAndLeviY
    self.NU_gridX = place_xy
    self.NU_gridY = place_z
    self.NU_leviX = place_xy
    self.NU_leviY = place_z
    
    offset_xy = self.NU_gridAndLeviOffsetX
    offset_z  = self.NU_gridAndLeviOffsetY
    self.NU_gridXoffset = offset_xy
    self.NU_gridYoffset = offset_z
    self.NU_leviXoffset = offset_xy
    self.NU_leviYoffset = offset_z

SIMPLE_OR_ADVANCED_ITEMS = [
    ('SIMPLE',  "Simple",  "Minimal settings"),
    ('ADVANCED', "Advanced", "Advanced settings"),
]

class PlacementProperties(bpy.types.PropertyGroup):
    LI_simpleOrAdvanced     : EnumProperty(items=SIMPLE_OR_ADVANCED_ITEMS)
    LI_simpleGridXY         : EnumProperty(items=getSimpleGridParams())
    LI_simpleGridZ          : EnumProperty(items=getSimpleGridParams())
    CB_syncGridLevi         : BoolProperty(name="Sync Grid & Levi steps",   default=True)
    NU_gridAndLeviX         : FloatProperty(name="Sync X",          default=8.0,       min=0,    soft_max=256, step=100, update=_updateGridAndLevi)
    NU_gridAndLeviY         : FloatProperty(name="Synx Y",          default=8.0,       min=0,    soft_max=256, step=100, update=_updateGridAndLevi)
    NU_gridAndLeviOffsetX   : FloatProperty(name="Sync X",          default=8.0,  soft_min=-256, soft_max=256, step=100, update=_updateGridAndLevi)
    NU_gridAndLeviOffsetY   : FloatProperty(name="Synx Y",          default=8.0,  soft_min=-256, soft_max=256, step=100, update=_updateGridAndLevi)
    NU_gridX                : FloatProperty(name="X Grid",          default=8.0,       min=0,    soft_max=256, step=100)
    NU_gridXoffset          : FloatProperty(name="X Offset",        default=0.0,  soft_min=-256, soft_max=256, step=100)
    NU_gridY                : FloatProperty(name="Y Grid",          default=8.0,       min=0,    soft_max=256, step=100)
    NU_gridYoffset          : FloatProperty(name="Y Offset",        default=0.0,  soft_min=-256, soft_max=256, step=100)
    NU_leviX                : FloatProperty(name="X Levitation",    default=8.0,       min=0,    soft_max=256, step=100)
    NU_leviXoffset          : FloatProperty(name="X Offset",        default=0.0,  soft_min=-256, soft_max=256, step=100)
    NU_leviY                : FloatProperty(name="Y Levitation",    default=8.0,       min=0,    soft_max=256, step=100)
    NU_leviYoffset          : FloatProperty(name="Y Offset",        default=0.0,  soft_min=-256, soft_max=256, step=100)
    CB_ghostMode            : BoolProperty(name="Ghostmode",        default=True)
    CB_autoRot              : BoolProperty(name="Auto Rotation",    default=False, description="Grid needs to be set to 0")
    CB_oneAxisRot           : BoolProperty(name="OneAxisRot",       default=False)
    CB_notOnItem            : BoolProperty(name="Not on Item",      default=True)
    CB_pivots               : BoolProperty(name="Pivots (ingame Q Key)",default=True)
    CB_pivotSwitch          : BoolProperty(name="Pivot switch",     default=False)
    NU_pivotSnapDis         : FloatProperty(name="Pivot snap distance", default=0.0,  min=0, soft_max=256, step=100)

    CB_placementCube        : BoolProperty(name="Placement Cube", default=False, description="Prevent item placement within the cube.")
    NU_cubeSize             : FloatProperty(name="Cube Size", default=0.0,  min=0, soft_max=256, step=100)
    PT_cubeCenter           : FloatVectorProperty(name="Cube Center", size=3, subtype='XYZ', default=(0.0, 0.0, 0.0), step=100)
    CB_attachmentConfiguration     : BoolProperty(name="Attachment Configuration", default=False, description="Enable attachment pattern for item placement onto blocks.")
    
    ST_sizeGroup            : StringProperty(name="Size Group",    default="0x0")
    CB_alwaysUp             : BoolProperty(name="Always Up",    default=False, description="Ensure items are always oriented upright during patch placement.")
    CB_alignToInterior      : BoolProperty(name="Align to Interior", default=False, description="Align items to the interior during patch placement.", update=_set_CB_alignToWorldDir_when_set_interior)
    CB_alignToWorldDir      : BoolProperty(name="Align to World Dir", default=False, description="Align items to the given world direction during patch placement.", update=_set_CB_alignToInterior_when_set_world)
    PT_worldDir             : FloatVectorProperty(name="World Dir", size=3, subtype='XYZ', default=(0.0, -1.0, 0.0), step=100)
    LI_compatibleGroups     : CollectionProperty(name="Compatible Groups", type=CompatiblePatchGroupProperty, description="Select compatible groups for item patch attachments.",)
    NU_compatibleGroups_index : IntProperty(name="Compatible Groups Index", default=-1)

    LI_patchLayouts         : CollectionProperty(name="Patch Layouts", type=PlacementPatchProperties, description="Define layouts for item patches.",)
    NU_patchLayouts_index   : IntProperty(name="Patch Layouts Index", default=-1)

    LI_pivots                : CollectionProperty(name="Pivots", type=PivotsProperties, description="Define pivot points for item placement.",)


