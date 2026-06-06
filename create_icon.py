"""
Luo yksinkertaisen icon.ico tiedoston jos sellaista ei ole.
Aja: python create_icon.py
Tarvitsee: pip install pillow
"""
try:
    from PIL import Image, ImageDraw, ImageFont
    import os

    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Tumma tausta
        draw.ellipse([2, 2, size-2, size-2], fill=(20, 27, 45, 255))

        # Vihreä kehä
        draw.ellipse([2, 2, size-2, size-2], outline=(82, 217, 160, 255),
                     width=max(1, size//16))

        # Käärme-emoji tekstinä (pienillä koolla yksinkertainen piste)
        emoji = "🐍"
        font_size = max(8, int(size * 0.55))
        try:
            font = ImageFont.truetype("seguiemj.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
                emoji = "BP"
            except:
                font = ImageFont.load_default()
                emoji = "B"

        bbox = draw.textbbox((0,0), emoji, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (size - tw) // 2
        y = (size - th) // 2
        draw.text((x, y), emoji, font=font, fill=(82, 217, 160, 255))
        images.append(img)

    images[0].save("icon.ico", format="ICO", sizes=[(s,s) for s in sizes],
                   append_images=images[1:])
    print("icon.ico created successfully")

except ImportError:
    print("Pillow not installed. Creating minimal icon...")
    # Luo minimaalinen ICO-tiedosto ilman Pillowia
    import struct

    def make_bmp(size):
        w = h = size
        # BITMAPINFOHEADER
        bih = struct.pack('<IiiHHIIiiII',
            40, w, -h, 1, 32, 0, w*h*4, 0, 0, 0, 0)
        # Pikselit — tumma vihreä
        pixels = b''
        for y in range(h):
            for x in range(w):
                cx, cy = x - w//2, y - h//2
                r = (cx*cx + cy*cy) ** 0.5
                if r < w//2 - 2:
                    pixels += bytes([45, 27, 20, 255])   # BGRA tumma
                elif r < w//2:
                    pixels += bytes([160, 217, 82, 255]) # BGRA vihreä kehä
                else:
                    pixels += bytes([0, 0, 0, 0])        # läpinäkyvä
        return bih + pixels

    sizes = [16, 32, 48, 256]
    bmps  = [make_bmp(s) for s in sizes]

    # ICO header
    header = struct.pack('<HHH', 0, 1, len(sizes))
    offset = 6 + len(sizes)*16
    directory = b''
    for i, s in enumerate(sizes):
        bmp = bmps[i]
        directory += struct.pack('<BBBBHHII',
            s if s < 256 else 0, s if s < 256 else 0,
            0, 0, 1, 32, len(bmp), offset)
        offset += len(bmp)

    with open("icon.ico","wb") as f:
        f.write(header + directory + b''.join(bmps))
    print("icon.ico created (minimal, no Pillow)")
