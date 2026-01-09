
# mstring.py
# string helpers (ONLY TWO NODES)

import re

# ====== M String Pick (index) ======
# In:  idx (INT), lines (STRING multiline)
# Out: text (STRING)
class MStringPickIndex:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "idx": ("INT", {"default": 0, "min": -(2**31), "max": (2**31 - 1), "step": 1}),
            "lines": ("STRING", {"default": "a\nb\nc", "multiline": True}),
        }}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "go"
    CATEGORY = "mnodes/string"

    def go(self, idx: int, lines: str):
        arr = [ln for ln in lines.splitlines() if ln.strip() != ""]
        if not arr:
            return ("",)
        if idx < 0 or idx >= len(arr):
            return ("",)
        return (arr[int(idx)],)


# ====== M Regex Replace (picked option) ======
# NOTE: input is named "n" (not "seed") to avoid ComfyUI's extra "control after generate" seed UI.
# In order: n, text, pattern, options, then regex settings
# Out order: next_seed, out_text, picked_option, picked_index
class MRegexReplaceFromLines:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "n": ("INT", {"default": 0, "min": 0, "max": 2**63 - 1, "step": 1}),

            # single-line input to save space
            "text": ("STRING", {"default": "", "multiline": False}),
            "pattern": ("STRING", {"default": "SKIN", "multiline": False}),

            # ONLY this is multiline
            "options": ("STRING", {"default": "pink\ngreen\nblue\n", "multiline": True}),

            "case_insensitive": ("BOOLEAN", {"default": False}),
            "multiline": ("BOOLEAN", {"default": False}),
            "dotall": ("BOOLEAN", {"default": True}),
            "max_replacements": ("INT", {"default": 0, "min": 0, "max": 999999, "step": 1}),  # 0=all
        }}

    RETURN_TYPES = ("INT", "STRING", "STRING", "INT")
    RETURN_NAMES = ("next_seed", "out_text", "picked_option", "picked_index")
    FUNCTION = "go"
    CATEGORY = "mnodes/string"

    def go(self, n: int, text: str, pattern: str, options: str,
           case_insensitive: bool, multiline: bool, dotall: bool, max_replacements: int):

        opts = [ln for ln in options.splitlines() if ln.strip() != ""]
        if not opts:
            return (int(n), text, "", 0)

        MASK64 = (1 << 64) - 1
        MASK63 = (1 << 63) - 1

        def splitmix64(x: int) -> int:
            x = (x + 0x9E3779B97F4A7C15) & MASK64
            z = x
            z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & MASK64
            z = (z ^ (z >> 27)) * 0x94D049BB133111EB & MASK64
            return (z ^ (z >> 31)) & MASK64

        r = splitmix64(int(n) & MASK64)
        picked_index = int(r % len(opts))
        picked_option = opts[picked_index]
        next_seed = int(r & MASK63)

        flags = 0
        if case_insensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE
        if dotall:
            flags |= re.DOTALL

        rx = re.compile(pattern, flags)
        out_text = rx.sub(picked_option, text, count=(max_replacements if max_replacements > 0 else 0))
        return (next_seed, out_text, picked_option, picked_index)


NODE_CLASS_MAPPINGS = {
    "MStringPickIndex": MStringPickIndex,
    "MRegexReplaceFromLines": MRegexReplaceFromLines,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MStringPickIndex": "M String Pick (index)",
    "MRegexReplaceFromLines": "M Regex Replace (picked option)",
}

