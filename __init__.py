
# __init__.py
from .mint import NODE_CLASS_MAPPINGS as MINT_C, NODE_DISPLAY_NAME_MAPPINGS as MINT_N
from .mstring import NODE_CLASS_MAPPINGS as MSTR_C, NODE_DISPLAY_NAME_MAPPINGS as MSTR_N
from .mutil import NODE_CLASS_MAPPINGS as MUTL_C, NODE_DISPLAY_NAME_MAPPINGS as MUTL_N

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

NODE_CLASS_MAPPINGS.update(MINT_C);  NODE_DISPLAY_NAME_MAPPINGS.update(MINT_N)
NODE_CLASS_MAPPINGS.update(MSTR_C);  NODE_DISPLAY_NAME_MAPPINGS.update(MSTR_N)
NODE_CLASS_MAPPINGS.update(MUTL_C);  NODE_DISPLAY_NAME_MAPPINGS.update(MUTL_N)

# serve frontend js from mnodes/js
WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

# API route for sidecar preview
import os, base64
from aiohttp import web
from server import PromptServer
import folder_paths

@PromptServer.instance.routes.get("/mnodes/lora_sidecar")
async def mnodes_lora_sidecar(request):
    name = request.rel_url.query.get("name", "")
    lora_path = folder_paths.get_full_path("loras", name)
    if not lora_path or not os.path.isfile(lora_path):
        return web.json_response({"error": "lora not found"}, status=404)

    base, _ = os.path.splitext(lora_path)
    txtp = base + ".txt"
    pngp = base + ".png"

    meta = ""
    if os.path.isfile(txtp):
        with open(txtp, "r", encoding="utf-8", errors="replace") as f:
            meta = f.read()

    thumb_b64 = ""
    if os.path.isfile(pngp):
        # keep it small, if your thumbs are huge, resize them earlier
        with open(pngp, "rb") as f:
            thumb_b64 = base64.b64encode(f.read()).decode("ascii")

    return web.json_response({"meta": meta, "thumb_b64": thumb_b64})

