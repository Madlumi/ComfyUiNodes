
# custom_nodes/mnodes/line_pick.py
# Pick a line from a multiline STRING using n % line_count.
# Good for palettes, prompt lists, etc.

class MLinePickModulo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "n": ("INT", {"default": 0, "min": -(2**31), "max": (2**31 - 1), "step": 1}),
            "i": ("STRING", {"default": "red\ngreen\nblue", "multiline": True}),
        }}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("o",)
    FUNCTION = "go"
    CATEGORY = "mnodes/string"

    def go(self, n: int, i: str):
        # split into lines, drop empty/whitespace-only lines
        lines = [ln for ln in i.splitlines() if ln.strip() != ""]
        if not lines:
            return ("",)

        idx = int(n) % len(lines)   # wraps automatically
        return (lines[idx],)


NODE_CLASS_MAPPINGS = {"MLinePickModulo": MLinePickModulo}
NODE_DISPLAY_NAME_MAPPINGS = {"MLinePickModulo": "M Line Pick (n % lines)"}

