import bpy
import os
from struct import pack, pack_into, unpack_from, calcsize
from collections import namedtuple

HeaderChunk = namedtuple("HeaderChunk", ["id", "size"])

class DataReader:
    index = 0

    def __init__(self, data):
        self.data = data

    def unpack(self, format):
        res = unpack_from(format, self.data, self.index)
        self.index += calcsize(format)
        return res

def transform_premul_px(px):
    r, g, b, a = px
    return (r*a, g*a, b*a, a)

def get_icon_data(icon_path):
    temp_icon_path = icon_path.replace(".tga", ".webp")

    # Load original TGA icon

    icon = bpy.data.images.load(icon_path).copy()

    # resize for TM
    icon.scale(64,64)

    # flip icon upside down and apply premultiplied alpha for TM
    for y in range(32):
        for x in range(64):
            idx_top = (y*64 + x) * 4
            idx_bottom = ((63-y) * 64 + x) * 4
            px_top = transform_premul_px(icon.pixels[idx_top : idx_top + 4])
            px_bottom = transform_premul_px(icon.pixels[idx_bottom : idx_bottom + 4])
            icon.pixels[idx_top : idx_top + 4] = px_bottom
            icon.pixels[idx_bottom : idx_bottom + 4] = px_top
    
    # ensure at least one pixel has a bit of transparence else TM won't decode the webp
    # because it has no alpha channel
    icon.pixels[3] = 0.99 

    # apply new pixels
    icon.update()

    # save icon as webp lossless for TM
    icon.file_format = "WEBP"
    icon.save(filepath=temp_icon_path, quality=100)

    # get icon data and remove temp file
    with open(temp_icon_path, "rb") as f:
        webp_data = f.read()

    os.remove(temp_icon_path)

    return webp_data

def set_icon(item_path, icon_path):
    
    webp_data = get_icon_data(icon_path)

    with open(item_path, "r+b") as f_item:
        # read item file
        icon_data = f_item.read()
        datar = DataReader(icon_data)

        # check version
        (version,) = datar.unpack("<3xH")
        if version != 6:
            return (1, f"GBX version not supported, must be 6, got {version}")
        
        # check class_id
        (class_id, ) = datar.unpack("<4xI")
        if class_id != 0x2e002000:
            return (2, f"Only Item.Gbx are supported, got class_id {hex(class_id)}")

        # header chunks
        index_user_data_size = datar.index
        (user_data_size, num_headerchunks) = datar.unpack("<II")

        chunks = []
        icon_chunk_idx = -1
        index_icon_chunk_size = -1

        for i in range(num_headerchunks):
            (chunk_id, chunk_size) = datar.unpack("<II")

            chunk_size &= 0x7FFFFFFF # remove heavy flag
            chunks.append(HeaderChunk(chunk_id, chunk_size))

            if chunk_id == 0x2e001004:
                icon_chunk_idx = i
                index_icon_chunk_size = datar.index - 4

        if icon_chunk_idx < 0:
            return (3, f"No existing icon chunk detected in the Item.Gbx")

        # read until icon chunk

        for chunk in chunks[:icon_chunk_idx]:
            datar.index += chunk.size

        # parse icon chunk

        old_icon_chunk = chunks[icon_chunk_idx]

        metadata = pack("<HHHI", 64 | 0x8000, 64 | 0x8000, 1, len(webp_data))
        icon_chunk = metadata + webp_data
        new_icon_chunk_size = len(icon_chunk)

        new_icon_data = bytearray(icon_data[:datar.index] + icon_chunk + icon_data[datar.index + old_icon_chunk.size:])

        # set new user_data_size
        pack_into("<I", new_icon_data, index_user_data_size, user_data_size - old_icon_chunk.size + new_icon_chunk_size)

        # set icon chunk size with heavy flag
        pack_into("<I", new_icon_data, index_icon_chunk_size, new_icon_chunk_size | 0x80000000)
        
        f_item.seek(0)
        f_item.write(new_icon_data)
        f_item.truncate()

    return (0, "")
