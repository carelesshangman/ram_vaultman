import ctypes, os, sys, time

k = ctypes.windll.kernel32
k.GetCurrentProcess.restype = ctypes.c_void_p
k.SetProcessWorkingSetSizeEx.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_ulong]
ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]


class Mem(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                ("free", ctypes.c_ulonglong)] + [(f"x{i}", ctypes.c_ulonglong) for i in range(5)]


class Proc(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + \
               [(n, ctypes.c_size_t) for n in ("peak", "ws", "a", "b", "c", "d", "pf", "pfpeak", "priv")]


def mem():
    m = Mem()
    m.len = ctypes.sizeof(m)
    k.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.total, m.free


def me():
    p = Proc()
    p.cb = ctypes.sizeof(p)
    ctypes.windll.psapi.GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(p), p.cb)
    return p.ws, p.priv


here = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
pics = []
for d in (os.path.join(here, "altmans"), os.path.join(getattr(sys, "_MEIPASS", here), "altmans")):
    if os.path.isdir(d):
        pics = [open(os.path.join(d, f), "rb").read() for f in os.listdir(d) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if pics:
        break

pic = b"".join(pics) or os.urandom(1 << 20)
CHUNK = 128 << 20
blob = pic * (CHUNK // len(pic))
per = CHUNK // len(pic) * len(pics)

k.SetConsoleTitleW("Sam is stealing your RAM")
print("Sam is stealing your RAM. ctrl+c to make him stop\n")

total, _ = mem()
keep = total * 0.01
vault = []
try:
    while True:
        total, free = mem()
        ws, priv = me()
        if vault and free < keep:
            vault.pop()
        elif free - keep > CHUNK and priv - ws < 2 << 30:
            vault.append(bytearray(blob))
        k.SetProcessWorkingSetSizeEx(k.GetCurrentProcess(), len(vault) * CHUNK + (256 << 20), total, 9)
        print(f"\r{(total - free) / total:.1%} used, {ws / 2**30:.1f} GB stolen, {len(vault) * per:,} sams in ram   ", end="", flush=True)
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\nfine. here's your ram back")
