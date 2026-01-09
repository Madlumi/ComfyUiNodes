
# custom_nodes/mnodes/mint.py
# "mint" = "M int" nodes, integer math toolkit for ComfyUI.

import math

I32_MIN = -(2**31)
I32_MAX =  (2**31 - 1)

def _int_socket(default=0):
    return ("INT", {"default": int(default), "min": I32_MIN, "max": I32_MAX, "step": 1})

def _safe_div(a: int, b: int) -> int:
    # Python // is floor division (matches math.floor(a/b)).
    # On b==0, return 0 instead of crashing.
    return 0 if b == 0 else (a // b)

def _safe_mod(a: int, b: int) -> int:
    # On b==0, return 0 instead of crashing.
    return 0 if b == 0 else (a % b)

def _lcm(a: int, b: int) -> int:
    # lcm(0, x) = 0
    if a == 0 or b == 0:
        return 0
    return abs(a // math.gcd(a, b) * b)

# ------------------------
# Binary ops
# ------------------------

class IntAdd:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("a_plus_b",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (a + b,)

class IntSub:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("a_minus_b",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (a - b,)

class IntMul:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(1), "b": _int_socket(1)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("a_times_b",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (a * b,)

class IntDivFloor:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(1)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("a_div_b_floor",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (_safe_div(a, b),)

class IntMod:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(1)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("a_mod_b",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (_safe_mod(a, b),)

class IntDivMod:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(1)}}
    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("quot", "rem")
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b):
        if b == 0:
            return (0, 0)
        q, r = divmod(a, b)
        return (q, r)

class IntPow:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(2), "b": _int_socket(8)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("a_pow_b",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b):
        # Keep it sane, huge exponents will explode time/size.
        b = max(min(int(b), 62), -62)
        if b < 0:
            return (0,)  # integer pow with negative exponent -> 0 (you can change this)
        return (int(pow(a, b)),)

class IntMin:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("min",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (a if a < b else b,)

class IntMax:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("max",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (a if a > b else b,)

class IntClamp:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"x": _int_socket(0), "lo": _int_socket(0), "hi": _int_socket(100)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("clamped",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, x, lo, hi):
        if lo > hi: lo, hi = hi, lo
        return (lo if x < lo else hi if x > hi else x,)

# ------------------------
# Unary ops
# ------------------------

class IntAbs:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"x": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("abs",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, x): return (abs(x),)

class IntNeg:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"x": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("neg",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, x): return (-x,)

class IntSign:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"x": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("sign",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, x):
        return (0 if x == 0 else (1 if x > 0 else -1),)

# ------------------------
# Number theory-ish
# ------------------------

class IntGCD:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("gcd",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (math.gcd(int(a), int(b)),)

class IntLCM:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("lcm",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (_lcm(int(a), int(b)),)

# ------------------------
# Comparisons -> INT booleans (0/1)
# ------------------------

class IntEq:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("a_eq_b",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (1 if a == b else 0,)

class IntLt:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("a_lt_b",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (1 if a < b else 0,)

class IntLe:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"a": _int_socket(0), "b": _int_socket(0)}}
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("a_le_b",)
    FUNCTION = "go"
    CATEGORY = "mnodes/int"
    def go(self, a, b): return (1 if a <= b else 0,)

# ------------------------
# ComfyUI discovery maps
# ------------------------

NODE_CLASS_MAPPINGS = {
    "MIntAdd": IntAdd,
    "MIntSub": IntSub,
    "MIntMul": IntMul,
    "MIntDivFloor": IntDivFloor,
    "MIntMod": IntMod,
    "MIntDivMod": IntDivMod,
    "MIntPow": IntPow,
    "MIntMin": IntMin,
    "MIntMax": IntMax,
    "MIntClamp": IntClamp,
    "MIntAbs": IntAbs,
    "MIntNeg": IntNeg,
    "MIntSign": IntSign,
    "MIntGCD": IntGCD,
    "MIntLCM": IntLCM,
    "MIntEq": IntEq,
    "MIntLt": IntLt,
    "MIntLe": IntLe,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MIntAdd": "M Int Add (a + b)",
    "MIntSub": "M Int Sub (a - b)",
    "MIntMul": "M Int Mul (a * b)",
    "MIntDivFloor": "M Int Div Floor (a // b)",
    "MIntMod": "M Int Mod (a % b)",
    "MIntDivMod": "M Int DivMod (q,r)",
    "MIntPow": "M Int Pow (a ** b)",
    "MIntMin": "M Int Min",
    "MIntMax": "M Int Max",
    "MIntClamp": "M Int Clamp",
    "MIntAbs": "M Int Abs",
    "MIntNeg": "M Int Neg",
    "MIntSign": "M Int Sign",
    "MIntGCD": "M Int GCD",
    "MIntLCM": "M Int LCM",
    "MIntEq": "M Int Eq (a==b)",
    "MIntLt": "M Int Lt (a<b)",
    "MIntLe": "M Int Le (a<=b)",
}

