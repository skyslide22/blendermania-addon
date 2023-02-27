from struct import pack_into, unpack_from, calcsize
from collections import namedtuple
from io import BytesIO
HeaderChunk = namedtuple("HeaderChunk", ["id", "size"])

class BufferReader:
    index = 0

    def __init__(self, buffer):
        self.buffer = buffer

    def unpack(self, format):
        res = unpack_from(format, self.buffer, self.index)
        self.index += calcsize(format)
        return res

def transform_px(px):
    r, g, b, a = px
    ratio = a / 255
    return (int(r*ratio), int(g*ratio), int(b*ratio), a)

def set_icon(path_item, path_icon):
    # import PIL here to prevent blandermania to crash if not installed
    from PIL import Image

    with Image.open(path_icon) as im:
        im = im.resize((64,64))
        
        out = BytesIO()
        for y in range(32):
            for x in range(64):
                px_top = im.getpixel((x, y))
                px_bottom = im.getpixel((x, 63-y))
                im.putpixel((x, y), transform_px(px_bottom))
                im.putpixel((x, 63-y), transform_px(px_top))
        im.save(out, "webp", lossless=True, quality=100, exact=True, method=4)
        webp_data = out.getvalue()

    with open(path_item, "r+b") as f_item:
        # read item file
        icon_data = f_item.read()
        br = BufferReader(icon_data)

        # check version
        (version,) = br.unpack("<3xH")
        if version < 6:
            return (1, f"GBX version not supported, must be at least 6, got {version}")
        
        # check class_id
        (class_id, ) = br.unpack("<4xI")
        if class_id != 0x2e002000:
            return (2, f"Only Item.Gbx are supported, got class_id {hex(class_id)}")

        # header chunks
        index_user_data_size = br.index
        (user_data_size, num_headerchunks) = br.unpack("<II")

        chunks = []
        icon_chunk_idx = -1
        index_icon_chunk_size = -1

        for i in range(num_headerchunks):
            (chunk_id, chunk_size) = br.unpack("<II")

            chunk_size &= 0x7FFFFFFF # remove heavy flag
            chunks.append(HeaderChunk(chunk_id, chunk_size))

            if chunk_id == 0x2e001004:
                icon_chunk_idx = i
                index_icon_chunk_size = br.index - 4

        if icon_chunk_idx < 0:
            return (3, f"No existing icon chunk detected in the Item.Gbx")

        # read until icon chunk

        for chunk in chunks[:icon_chunk_idx]:
            br.unpack(f"{chunk.size}x")

        icon_chunk = chunks[icon_chunk_idx]

        # parse icon chunk

        (width, height) = br.unpack("<HH")
        is_webp = ((width & 0x8000) == 0x8000) and ((height & 0x8000) == 0x8000)

        if not is_webp:
            return (4, f"Icon is not is webp format, can't fix it")

        (_u01, old_webp_data_size) = br.unpack(f"<HI")

        offset_len = len(webp_data) - old_webp_data_size

        new_icon_data = bytearray(icon_data[:br.index] + webp_data + icon_data[br.index+old_webp_data_size:])
        # set new user_data_size
        pack_into("<I", new_icon_data, index_user_data_size, user_data_size + offset_len)
        # set icon chunk size with heavy flag
        pack_into("<I", new_icon_data, index_icon_chunk_size, (icon_chunk.size + offset_len) | 0x80000000)
        # set webp size
        pack_into("<I", new_icon_data, br.index - 4, old_webp_data_size + offset_len)
        
        f_item.seek(0)
        f_item.write(new_icon_data)
        f_item.truncate()

    return (0, "")

if __name__ == '__main__':
    set_icon("test-icon.Item.Gbx", "test-icon.tga")