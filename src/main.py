import os
import random
from datetime import datetime

import torch
from diffusers import StableDiffusionPipeline
import pandas as pd
import gradio as gr
import yaml

# =======================
# CONFIGURACIÓN
# =======================
CONFIG_PATH = "config.yaml"

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
else:
    config = {
        "model_name": "runwayml/stable-diffusion-v1-5",
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "height": 512,
        "width": 512,
        "num_inference_steps": 50,
        "guidance_scale": 7.5,
        "seed": None,
        "output_dir": "data/generated"
    }

os.makedirs(config["output_dir"], exist_ok=True)

# =======================
# CARGA DEL MODELO
# =======================
print("Cargando modelo...")
pipe = StableDiffusionPipeline.from_pretrained(
    config["model_name"], torch_dtype=torch.float16 if config["device"]=="cuda" else torch.float32
)
pipe = pipe.to(config["device"])
pipe.enable_attention_slicing()  # reduce uso de memoria

# =======================
# FUNCIÓN DE GENERACIÓN
# =======================
def generate_image(prompt: str, height=None, width=None, steps=None, guidance=None, seed=None):
    height = height or config["height"]
    width = width or config["width"]
    steps = steps or config["num_inference_steps"]
    guidance = guidance or config["guidance_scale"]
    seed = seed or config["seed"] or random.randint(0, 2**32 - 1)

    generator = torch.Generator(device=config["device"]).manual_seed(seed)
    image = pipe(prompt, height=height, width=width, num_inference_steps=steps, guidance_scale=guidance, generator=generator).images[0]

    # Guardar imagen
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_seed{seed}.png"
    path = os.path.join(config["output_dir"], filename)
    image.save(path)

    # Guardar metadata
    meta_path = os.path.join(config["output_dir"], "metadata.csv")
    meta_data = pd.DataFrame([{
        "filename": filename,
        "prompt": prompt,
        "height": height,
        "width": width,
        "steps": steps,
        "guidance": guidance,
        "seed": seed,
        "timestamp": timestamp
    }])
    if os.path.exists(meta_path):
        meta_data.to_csv(meta_path, mode="a", header=False, index=False)
    else:
        meta_data.to_csv(meta_path, index=False)

    return image

# =======================
# INTERFAZ GRADIO
# =======================
def gradio_interface(prompt, height, width, steps, guidance, seed):
    img = generate_image(prompt, height, width, steps, guidance, seed)
    return img

iface = gr.Interface(
    fn=gradio_interface,
    inputs=[
        gr.Textbox(label="Prompt"),
        gr.Number(label="Height", value=config["height"]),
        gr.Number(label="Width", value=config["width"]),
        gr.Number(label="Steps", value=config["num_inference_steps"]),
        gr.Number(label="Guidance Scale", value=config["guidance_scale"]),
        gr.Number(label="Seed (opcional)", value=config["seed"] or 0)
    ],
    outputs=gr.Image(type="pil"),
    title="Generador de Imágenes IA",
    description="Genera imágenes con Stable Diffusion. Guarda imagen y metadata automáticamente."
)

if __name__ == "__main__":
    iface.launch()
