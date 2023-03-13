import bpy
import os
from struct import pack, pack_into, unpack_from, calcsize
from collections import namedtuple

HeaderChunk = namedtuple("HeaderChunk", ["id", "size"])

class BinaryReader:
    index = 0

    def __init__(self, data):
        self.data = data

    def unpack(self, format):
        res = unpack_from(format, self.data, self.index)
        self.index += calcsize(format)
        return res

def get_icon_chunk(icon_path):
    # Load original TGA icon
    icon = bpy.data.images.load(icon_path)

    # resize for TM
    icon.scale(64,64)
    
    # ensure at least one pixel has a bit of transparence else
    # it won't work if TM convert it to webp
    if icon.pixels[3] > 0.99:
        icon.pixels[3] = 0.99

    # Create the chunk
    chunk = bytearray(64*64*4)
    for y in range(63, -1, -1):
        for x in range(64):
            idx = (y * 64 + x) * 4
            chunk[idx + 0] = int(icon.pixels[idx + 2] * 255)
            chunk[idx + 1] = int(icon.pixels[idx + 1] * 255)
            chunk[idx + 2] = int(icon.pixels[idx + 0] * 255)
            chunk[idx + 3] = int(icon.pixels[idx + 3] * 255)
    
    # Close icon file
    bpy.data.images.remove(icon)

    return pack("<HH", 64, 64) + chunk

def set_icon(item_path, icon_path):
    
    icon_chunk = get_icon_chunk(icon_path)

    with open(item_path, "r+b") as f_item:
        # read item file
        item_data = f_item.read()
        byter = BinaryReader(item_data)

        # check version
        (version,) = byter.unpack("<3xH")
        if version != 6:
            return (1, f"GBX version not supported, must be 6, got {version}")
        
        # check class_id
        (class_id, ) = byter.unpack("<4xI")
        if class_id != 0x2e002000:
            return (2, f"Only Item.Gbx are supported, got class_id {hex(class_id)}")

        # header chunks
        index_user_data_size = byter.index
        (user_data_size, num_headerchunks) = byter.unpack("<II")

        chunks = []
        icon_chunk_idx = -1
        index_icon_chunk_size = -1

        for i in range(num_headerchunks):
            (chunk_id, chunk_size) = byter.unpack("<II")

            chunk_size &= 0x7FFFFFFF # remove heavy flag
            chunks.append(HeaderChunk(chunk_id, chunk_size))

            if chunk_id == 0x2e001004:
                icon_chunk_idx = i
                index_icon_chunk_size = byter.index - 4

        if icon_chunk_idx < 0:
            return (3, f"No existing icon chunk detected in the Item.Gbx")

        # read until icon chunk

        for chunk in chunks[:icon_chunk_idx]:
            byter.index += chunk.size

        # overwrite icon chunk

        old_icon_chunk_size = chunks[icon_chunk_idx].size
        new_icon_chunk_size = len(icon_chunk)

        new_item_data = bytearray(item_data[:byter.index] + icon_chunk + item_data[byter.index + old_icon_chunk_size:])

        # set new user_data_size
        pack_into("<I", new_item_data, index_user_data_size, user_data_size - old_icon_chunk_size + new_icon_chunk_size)

        # set new icon chunk size with heavy flag
        pack_into("<I", new_item_data, index_icon_chunk_size, new_icon_chunk_size | 0x80000000)
        
        f_item.seek(0)
        f_item.write(new_item_data)
        f_item.truncate()

    return (0, "")
