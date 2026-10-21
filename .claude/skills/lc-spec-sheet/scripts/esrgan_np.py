"""Real-ESRGAN x4plus (RRDBNet) inference in plain numpy, no torch.

    python3 -I esrgan_np.py weights.pth in.png out.png

The .pth is read with a restricted unpickler that only builds float tensors.
"""
import sys, zipfile, pickle, collections
import numpy as np
from PIL import Image


class _Storage:
    def __init__(self, key, dtype):
        self.key, self.dtype = key, dtype


def load_pth(path):
    z = zipfile.ZipFile(path)
    root = z.namelist()[0].split("/")[0]
    dtypes = {"FloatStorage": np.float32, "HalfStorage": np.float16}

    def rebuild(storage, offset, size, stride, *rest):
        buf = np.frombuffer(z.read(f"{root}/data/{storage.key}"), dtype=storage.dtype)
        n = int(np.prod(size)) if size else 1
        a = buf[offset:offset + max(1, sum((s - 1) * st for s, st in zip(size, stride)) + 1)]
        return np.lib.stride_tricks.as_strided(a, shape=size, strides=[s * a.itemsize for s in stride]).astype(np.float32).copy() if size else a[:1].astype(np.float32)

    class U(pickle.Unpickler):
        def find_class(self, mod, name):
            if (mod, name) == ("collections", "OrderedDict"):
                return collections.OrderedDict
            if (mod, name) == ("torch._utils", "_rebuild_tensor_v2"):
                return rebuild
            if mod == "torch" and name in dtypes:
                return name
            raise pickle.UnpicklingError(f"refused {mod}.{name}")

        def persistent_load(self, pid):
            _, stype, key, _loc, _n = pid
            return _Storage(key, dtypes[stype])

    return U(z.open(f"{root}/data.pkl")).load()


def conv(x, w, b):
    """x: (C,H,W); w: (O,C,3,3) -> (O,H,W), padding 1."""
    C, H, W = x.shape
    p = np.pad(x, ((0, 0), (1, 1), (1, 1)))
    cols = np.empty((C, 9, H, W), np.float32)
    for i in range(3):
        for j in range(3):
            cols[:, i * 3 + j] = p[:, i:i + H, j:j + W]
    out = w.reshape(w.shape[0], -1) @ cols.reshape(C * 9, H * W)
    return (out + b[:, None]).reshape(-1, H, W)


lrelu = lambda x: np.where(x > 0, x, 0.2 * x)


def rrdbnet(P, x):
    c = lambda name, t: conv(t, P[name + ".weight"], P[name + ".bias"])
    fea = c("conv_first", x)
    body = fea
    for i in range(23):
        rin = body
        for k in (1, 2, 3):
            t = body
            feats = [t]
            for n in range(1, 5):
                feats.append(lrelu(c(f"body.{i}.rdb{k}.conv{n}", np.concatenate(feats))))
            body = c(f"body.{i}.rdb{k}.conv5", np.concatenate(feats)) * 0.2 + t
        body = body * 0.2 + rin
    fea = fea + c("conv_body", body)
    up = lambda t: t.repeat(2, axis=1).repeat(2, axis=2)
    fea = lrelu(c("conv_up1", up(fea)))
    fea = lrelu(c("conv_up2", up(fea)))
    return c("conv_last", lrelu(c("conv_hr", fea)))


def main(wpath, src, out, tile=96, pad=10):
    sd = load_pth(wpath)
    P = sd.get("params_ema") or sd.get("params") or sd
    img = np.asarray(Image.open(src).convert("RGB"), np.float32).transpose(2, 0, 1) / 255
    _, H, W = img.shape
    res = np.zeros((3, H * 4, W * 4), np.float32)
    for y0 in range(0, H, tile):
        for x0 in range(0, W, tile):
            y1, x1 = min(y0 + tile, H), min(x0 + tile, W)
            ya, xa, yb, xb = max(0, y0 - pad), max(0, x0 - pad), min(H, y1 + pad), min(W, x1 + pad)
            o = rrdbnet(P, img[:, ya:yb, xa:xb])
            res[:, y0 * 4:y1 * 4, x0 * 4:x1 * 4] = o[:, (y0 - ya) * 4:(y0 - ya + y1 - y0) * 4, (x0 - xa) * 4:(x0 - xa + x1 - x0) * 4]
            print("tile", y0, x0, flush=True)
    Image.fromarray((np.clip(res, 0, 1).transpose(1, 2, 0) * 255 + 0.5).astype(np.uint8)).save(out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
