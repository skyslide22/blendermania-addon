import bpy
from bpy.props import *


# mirrors the enums of ItemPlacementUtils (GetPlacement*Tag), values as they are written into the item config
ATTACHMENT_KEY_TYPE        = "Type"
ATTACHMENT_KEY_SIZE        = "Size"
ATTACHMENT_KEY_PILOT_SLOT  = "PilotSlot"
ATTACHMENT_KEY_SLOT        = "Slot"
ATTACHMENT_KEY_PLACEMENT   = "Placement"
ATTACHMENT_KEY_VARIANT     = "Variant"
ATTACHMENT_KEY_MAT_MODIFIER = "MatModifier"

# slots are written as zero padded integers: 01, 02, ...
ATTACHMENT_INT_KEYS = (ATTACHMENT_KEY_SLOT, ATTACHMENT_KEY_PILOT_SLOT)

ATTACHMENT_KNOWN_VALUES: dict[str, tuple[str, ...]] = {
    ATTACHMENT_KEY_TYPE: (
        "Bush", "Cactus", "CherryTree", "Cypress", "CypressDirt", "Fir", "FirSnow", "Flag", "Flower", "Fogger",
        "Lamp", "LightTube", "PalmTree", "PalmTreeSugar", "Pillar", "Plant", "Podium", "Ramp", "Rig", "RoadSign",
        "RotorFrame", "Screen", "Show", "Spectator", "SpringTree", "SupportTruss", "SupportTrussConnector",
        "TrackBarrier", "Tree", "TreeBushy", "TreeFir", "TreePineDead", "TreeThin", "TreeThinBushy",
        "TunnelSupportArch", "TunnelSupportArchCenter", "TunnelSupportHalfArch", "TunnelSupportPillar",
        "TunnelSupportPillarLarge",
    ),
    ATTACHMENT_KEY_SIZE: (
        "16m", "1x1", "2m", "2x1", "32m", "4m", "6x1", "8m", "Big", "Curve1", "Curve2", "Curve3",
        "Medium", "Small", "Tall", "VerySmall",
    ),
    ATTACHMENT_KEY_PLACEMENT: (
        "Back", "BackStage", "Ecotone", "Forest", "Front", "Grove", "PalmEcotone", "PalmForest", "PalmGrove",
        "Show", "ShowFull", "ShowRace", "Synthetic", "Top/Bottom", "Wild",
    ),
    ATTACHMENT_KEY_VARIANT: (
        "A", "B", "C", "D", "DiagCube", "DiagSquare", "E", "F", "In", "Light", "OnTruss", "OnTruss16m",
        "OnTruss8m", "Out", "Speaker", "Str", "Curve",
    ),
    ATTACHMENT_KEY_MAT_MODIFIER: ("Dirt", "Grass", "Ice"),
}

# order in the ui
ATTACHMENT_KNOWN_KEYS = (
    ATTACHMENT_KEY_TYPE,
    ATTACHMENT_KEY_SIZE,
    ATTACHMENT_KEY_PILOT_SLOT,
    ATTACHMENT_KEY_SLOT,
    ATTACHMENT_KEY_PLACEMENT,
    ATTACHMENT_KEY_VARIANT,
    ATTACHMENT_KEY_MAT_MODIFIER,
)


def format_attachment_slot(value: int) -> str:
    return f"{int(value):02d}"


def _key_search(self, context, edit_text):
    needle = edit_text.lower()
    return [k for k in ATTACHMENT_KNOWN_KEYS if needle in k.lower()]

def _value_search(self, context, edit_text):
    needle = edit_text.lower()
    return [v for v in ATTACHMENT_KNOWN_VALUES.get(self.key, ()) if needle in v.lower()]


class AttachmentOptionEntryProperties(bpy.types.PropertyGroup):
    """one key/value pair of an attachment option"""
    key: StringProperty(
        name="Key",
        description="Option key, pick a known one or write your own",
        default=ATTACHMENT_KEY_TYPE,
        search=_key_search,
        search_options={'SUGGESTION'},
    )
    value: StringProperty(
        name="Value",
        description="Option value, pick a known one or write your own",
        default="",
        search=_value_search,
        search_options={'SUGGESTION'},
    )
    intValue: IntProperty(
        name="Value",
        description="Slot number, written as 01, 02, ...",
        default=1, min=0, max=99,
    )


class AttachmentOptionProperties(bpy.types.PropertyGroup):
    """one option (set of key/value pairs) of an attachment definition"""
    entries: CollectionProperty(name="Entries", type=AttachmentOptionEntryProperties)
    entries_index: IntProperty(name="Entries Index", default=-1)


class AttachmentProperties(bpy.types.PropertyGroup):
    """attachment definition of a collection inside an attachments collection"""
    layout: IntProperty(
        name="Layout",
        description="Layout index/id of the attachment definition",
        default=0, min=0,
    )
    options: CollectionProperty(name="Options", type=AttachmentOptionProperties)
    options_index: IntProperty(name="Options Index", default=-1)


def get_attachment_option_dicts(attachment: AttachmentProperties) -> list[dict[str, str]]:
    """options as written into the config, empty keys/values are skipped, empty options dropped"""
    options: list[dict[str, str]] = []
    for option in attachment.options:
        pairs: dict[str, str] = {}
        for entry in option.entries:
            key = entry.key.strip()
            if not key:
                continue
            if key in ATTACHMENT_INT_KEYS:
                pairs[key] = format_attachment_slot(entry.intValue)
            elif entry.value.strip():
                pairs[key] = entry.value.strip()
        if pairs:
            options.append(pairs)
    return options
