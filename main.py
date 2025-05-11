from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image
import io
import numpy as np
from rembg import remove

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def remove_background(image: Image.Image) -> Image.Image:
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    output = remove(img_bytes.read())
    return Image.open(io.BytesIO(output)).convert("RGBA")

def compose_bouquet(images: list[Image.Image], quantity: int) -> Image.Image:
    canvas = Image.new("RGBA", (800, 800), (255, 255, 255, 0))
    angle_step = 360 / max(quantity, 1)
    center = (400, 400)
    radius = 250

    for i in range(min(quantity, len(images))):
        angle = i * angle_step
        flower = images[i % len(images)].resize((150, 150))
        x = int(center[0] + radius * np.cos(np.radians(angle)) - 75)
        y = int(center[1] + radius * np.sin(np.radians(angle)) - 75)
        canvas.paste(flower, (x, y), flower)

    return canvas

@app.post("/generate")
async def generate_bouquet(images: list[UploadFile] = File(...), quantity: int = Form(...)):
    flower_imgs = []
    for file in images:
        img = Image.open(io.BytesIO(await file.read())).convert("RGBA")
        img = remove_background(img)
        flower_imgs.append(img)

    bouquet = compose_bouquet(flower_imgs, int(quantity))
    buf = io.BytesIO()
    bouquet.save(buf, format='PNG')
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
