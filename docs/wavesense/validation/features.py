"""WaveSense pipeline pieces: windowing + statistical features."""
import numpy as np

WIN = 400  # 4 s at 100 Hz

def valid_subcarriers(A_all, thr=0.5):
    """Data-driven empty/null subcarrier removal: keep slots whose mean amplitude > thr."""
    return np.where(A_all.mean(0) > thr)[0]

def windows(A, win=WIN):
    n = len(A) // win
    return A[: n * win].reshape(n, win, A.shape[1])

def _entropy(x, bins=20):
    h, _ = np.histogram(x, bins=bins)
    p = h / max(h.sum(), 1); p = p[p > 0]
    return -(p * np.log2(p)).sum()

def _dyn(W):
    """Per-subcarrier dynamic features on (n, T, S): std, range, mean |diff| + aggregated."""
    D = W - W.mean(1, keepdims=True)  # static component removed
    std = D.std(1); rng = D.max(1) - D.min(1); dif = np.abs(np.diff(W, axis=1)).mean(1)
    agg = np.stack([std.mean(1), (D ** 2).mean((1, 2)),  # mean std, energy (= mean variance)
                    std.max(1), dif.mean(1),
                    np.array([_entropy((d / (d.std() + 1e-9)).ravel()) for d in D])], 1)
    return np.concatenate([std, rng, dif, agg], 1)

def feat_raw(W):
    """Mean (absolute level) + dynamics. Absolute level is environment/gain dependent."""
    return np.concatenate([W.mean(1), _dyn(W)], 1)

def feat_dyn(W):
    """Static component removed: dynamics only."""
    return _dyn(W)

def feat_rel(W):
    """Gain-invariant: divide each subcarrier by its window mean, then dynamics (coef. of variation)."""
    return _dyn(W / (W.mean(1, keepdims=True) + 1e-6))

FEATS = {'raw': feat_raw, 'dyn': feat_dyn, 'rel': feat_rel}

def augment(W, rng, n_copies=2):
    """Cheap CSI augmentations: random global + smooth per-subcarrier gain, additive noise."""
    out = []
    S = W.shape[2]
    for _ in range(n_copies):
        g = rng.uniform(0.7, 1.4, size=(len(W), 1, 1))
        k = np.linspace(0, np.pi, S)[None, None, :]
        shape = 1 + 0.15 * np.sin(k * rng.uniform(0.5, 3, size=(len(W), 1, 1)) + rng.uniform(0, 6.3, size=(len(W), 1, 1)))
        noise = rng.normal(0, 0.5, size=W.shape).astype(np.float32)
        out.append((W * g * shape + noise).astype(np.float32))
    return np.concatenate(out)
