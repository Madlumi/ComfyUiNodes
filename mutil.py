
# mutil.py
# Utility nodes for ComfyUI (mnodes)

import os
import re

import numpy as np
import torch
from PIL import Image

import folder_paths
import comfy.sd
import comfy.utils


def _sidecar_paths(lora_full_path: str):
    base, _ = os.path.splitext(lora_full_path)
    return base + ".png", base + ".txt"


def _load_thumb_as_image_tensor(png_path: str):
    # ComfyUI IMAGE tensor: [1, H, W, 3], float32 0..1
    if not os.path.isfile(png_path):
        return torch.zeros((1, 64, 64, 3), dtype=torch.float32)

    im = Image.open(png_path).convert("RGB")
    arr = np.asarray(im).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None, ...]


def _read_text(path: str):
    if not os.path.isfile(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _guess_weight_from_text(txt: str):
    # recommendedWeight:"0.7" (your txt format)
    m = re.search(r'recommendedWeight\s*:\s*"?([0-9]+(?:\.[0-9]+)?)"?', txt, re.I)
    if m:
        return float(m.group(1))
    # <lora:name:0.7> (common prompt format)
    m = re.search(r"<lora:[^:>]+:([0-9]+(?:\.[0-9]+)?)>", txt, re.I)
    if m:
        return float(m.group(1))
    return None


class MGroupInputs:
    """
    Group common workflow inputs into one node.

    Outputs:
      prompt, negative, seed,
      width, height, batch_size,
      steps, cfg, sampler_name, scheduler, denoise,
      ckpt_name, filename_prefix,
      5x (lora_name, lora_strength) where strength can feed both model+clip.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"default": "", "multiline": True}),
            "negative": ("STRING", {"default": "", "multiline": True}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 2**63 - 1, "step": 1}),
            "width": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
            "height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
            "batch_size": ("INT", {"default": 1, "min": 1, "max": 64, "step": 1}),
            "steps": ("INT", {"default": 25, "min": 1, "max": 200, "step": 1}),
            "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 30.0, "step": 0.1}),
            "sampler_name": ("SAMPLER_NAME",),
            "scheduler": ("SCHEDULER_NAME",),
            "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            "ckpt_name": ("CKPT_NAME",),
            "filename_prefix": ("STRING", {"default": "ComfyUI", "multiline": False}),
            "lora1": ("LORA_NAME",),
            "lora1_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.05}),
            "lora2": ("LORA_NAME",),
            "lora2_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.05}),
            "lora3": ("LORA_NAME",),
            "lora3_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.05}),
            "lora4": ("LORA_NAME",),
            "lora4_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.05}),
            "lora5": ("LORA_NAME",),
            "lora5_strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.05}),
        }}

    RETURN_TYPES = (
        "STRING", "STRING", "INT",
        "INT", "INT", "INT",
        "INT", "FLOAT", "SAMPLER_NAME", "SCHEDULER_NAME", "FLOAT",
        "CKPT_NAME", "STRING",
        "LORA_NAME", "FLOAT",
        "LORA_NAME", "FLOAT",
        "LORA_NAME", "FLOAT",
        "LORA_NAME", "FLOAT",
        "LORA_NAME", "FLOAT",
    )

    RETURN_NAMES = (
        "prompt", "negative", "seed",
        "width", "height", "batch_size",
        "steps", "cfg", "sampler_name", "scheduler", "denoise",
        "ckpt_name", "filename_prefix",
        "lora1", "lora1_strength",
        "lora2", "lora2_strength",
        "lora3", "lora3_strength",
        "lora4", "lora4_strength",
        "lora5", "lora5_strength",
    )

    FUNCTION = "go"
    CATEGORY = "mnodes/util"

    def go(self, **kw):
        return tuple(kw[name] for name in self.RETURN_NAMES)


class MExtendedLoraLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "model": ("MODEL",),
            "clip": ("CLIP",),

            # real dropdown (same idea as Comfy's loader)
            "lora_name": (folder_paths.get_filename_list("loras"),),

            "strength_model": ("FLOAT", {"default": 0.8, "min": -5.0, "max": 5.0, "step": 0.05}),
            "strength_clip": ("FLOAT", {"default": 0.8, "min": -5.0, "max": 5.0, "step": 0.05}),
            "auto_strength_from_meta": ("BOOLEAN", {"default": True}),
        }}

    RETURN_TYPES = ("MODEL", "CLIP", "IMAGE", "STRING", "STRING", "FLOAT", "FLOAT")
    RETURN_NAMES = ("model", "clip", "thumb", "meta_text", "lora_name", "strength_model", "strength_clip")
    FUNCTION = "load"
    CATEGORY = "mnodes/util"

    def load(self, model, clip, lora_name, strength_model, strength_clip, auto_strength_from_meta):
        lora_path = folder_paths.get_full_path("loras", lora_name)
        if lora_path is None or not os.path.isfile(lora_path):
            raise FileNotFoundError(f"LoRA not found: {lora_name}")

        thumb_path, meta_path = _sidecar_paths(lora_path)
        meta_text = _read_text(meta_path)
        thumb = _load_thumb_as_image_tensor(thumb_path)

        if auto_strength_from_meta and meta_text:
            w = _guess_weight_from_text(meta_text)
            if w is not None:
                strength_model = w
                strength_clip = w

        lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
        model_lora, clip_lora = comfy.sd.load_lora_for_models(
            model, clip, lora, strength_model, strength_clip
        )

        ui = {"text": [meta_text if meta_text else "(no .txt sidecar)"]}
        return {"ui": ui, "result": (model_lora, clip_lora, thumb, meta_text, lora_name, strength_model, strength_clip)}


NODE_CLASS_MAPPINGS = {
    "MGroupInputs": MGroupInputs,
    "MExtendedLoraLoader": MExtendedLoraLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MGroupInputs": "M Group Inputs",
    "MExtendedLoraLoader": "M Extended LoRA Loader (thumb+meta)",
}

