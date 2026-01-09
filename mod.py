
# custom_nodes/mnodes/mod.py
#
# Minimal ComfyUI custom node: integer modulo (a % b).
# Drop this file under: custom_nodes/mnodes/mod.py
# Make sure you also have: custom_nodes/mnodes/__init__.py that imports this module.

class IntModulo:
    @classmethod
    def INPUT_TYPES(cls):
        # ComfyUI uses this to build the node UI.
        # "required" means the node will always show these inputs.
        return {"required": {
            # ("INT", {...}) declares an integer socket with UI metadata.
            "a": ("INT", {"default": 0, "min": -2**31, "max": 2**31 - 1, "step": 1}),
            "b": ("INT", {"default": 1, "min": -2**31, "max": 2**31 - 1, "step": 1}),
        }}

    # What types this node outputs (one INT).
    RETURN_TYPES = ("INT",)

    # Friendly name for the output socket.
    RETURN_NAMES = ("a_mod_b",)

    # Which method to call when the node executes.
    FUNCTION = "mod"

    # Where the node appears in the right-click menu.
    CATEGORY = "mnodes/math"

    def mod(self, a: int, b: int):
        # Avoid crashing on divide-by-zero.
        # You can change this behavior (raise, clamp, etc) if you prefer.
        if b == 0:
            return (0,)
        return (a % b,)


# ComfyUI discovers nodes via these two dicts.
# Keys must be unique across all loaded custom nodes.
NODE_CLASS_MAPPINGS = {
    "IntModulo": IntModulo,
}

# What shows in the UI for the node name.
NODE_DISPLAY_NAME_MAPPINGS = {
    "IntModulo": "Int Modulo (a % b)",
}

