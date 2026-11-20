"""False-alarm reduction experiments on Wallhack1.8k presence.
Baseline = change features + fixed 2-min empty-room calibration (z-score per setting), LR / RF.
All tuning (decision thresholds) uses only training folds (inner out-of-fold predictions) or the
test setting's own 2-min empty calibration (available at install time). Fixed seeds."""
import sys, json, numpy as np, pandas as pd
from scipy.ndimage import median_filter
from scipy.signal import butter, lfilter
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold
from sklearn.covariance import LedoitWolf
from sklearn.decomposition import PCA
from load_wallhack import recordings, load_file
from features import valid_subcarriers, _entropy

SEED = 0; WIN = 400; CAL = 0.2; FS = 100
SETTINGS = ['LOS-BQ', 'LOS-PIFA', 'NLOS-BQ', 'NLOS-PIFA']
recs = recordings(); amps = {r['rec']: load_file(r['path'])[0] for r in recs}
V = valid_subcarriers(np.concatenate(list(amps.values())))

# ---------------- preprocessing (applied to the continuous amplitude series of a recording, causal) ----------------
def hampel(A, k=7, nsig=3.0):
    med = median_filter(A, size=(k, 1), mode='nearest')
    mad = 1.4826 * median_filter(np.abs(A - med), size=(k, 1), mode='nearest')
    out = A.copy(); bad = np.abs(A - med) > nsig * (mad + 1e-6); out[bad] = med[bad]; return out
_b, _a = butter(4, 10 / (FS / 2))  # 10 Hz low-pass (human motion < ~10 Hz)
def lowpass(A): return lfilter(_b, _a, A, axis=0)
def movavg(A, n=10):
    c = np.cumsum(np.vstack([np.zeros((1, A.shape[1])), A]), 0); out = (c[n:] - c[:-n]) / n
    return np.vstack([np.repeat(out[:1], n - 1, 0), out])
def ratio(A):  # amplitude ratio of adjacent subcarriers: cancels common gain/AGC fluctuation (phase-free)
    return A[:, :-1] / (A[:, 1:] + 1e-6)
PRE = {'none': lambda A: A, 'hampel': hampel, 'hampel+lowpass': lambda A: lowpass(hampel(A)),
       'movavg': movavg, 'ratio': ratio, 'hampel+ratio': lambda A: ratio(hampel(A))}

def change_feats(W, prev_mean, relative=True):
    D = W - W.mean(1, keepdims=True)
    std = D.std(1); var = std ** 2; de = (np.diff(W, axis=1) ** 2).mean(1)
    pc = np.abs(W.mean(1) - prev_mean) / ((np.abs(prev_mean) + 1e-6) if relative else 1.0)
    agg = np.stack([std.mean(1), var.mean(1), de.mean(1), pc.mean(1),
                    np.array([_entropy((d / (d.std() + 1e-9)).ravel()) for d in D])], 1)
    return np.concatenate([std, var, de, pc, agg], 1)

def build(pre='none', hop=WIN, pca=False):
    """Windows (WIN packets, given hop) for every recording; features + meta. Windows need a previous
    window (start-WIN) in the same recording. Empty recording: first 20% packets = calibration; eval windows
    must not overlap calibration and must not straddle the 5 time blocks used for grouping."""
    F, M = [], []
    for s in SETTINGS:
        scen, sysm = s.split('-')
        rs = [r for r in recs if r['scen'] == scen and r['sys'] == sysm]
        series = {r['rec']: PRE[pre](amps[r['rec']][:, V].astype(np.float64)) for r in rs}
        if pca:  # fit on calibration packets of this setting; drop 1st (static) component, keep next 5
            b = [r for r in rs if r['act'] == 0][0]; A = series[b['rec']]; ncp = int(len(A) * CAL)
            p = PCA(6, random_state=SEED).fit(A[:ncp]); series = {k: p.transform(v)[:, 1:] for k, v in series.items()}
        for r in rs:
            A = series[r['rec']]; n = len(A); empty = r['act'] == 0
            ncp = int(n * CAL) if empty else 0
            starts = np.arange(WIN, n - WIN + 1, hop)  # needs previous window [st-WIN, st)
            for st in starts:
                W = A[st:st + WIN][None]; prev = A[st - WIN:st].mean(0)[None]
                calib = empty and st + WIN <= ncp
                if empty and not calib:
                    if st - WIN < ncp: continue  # previous window overlaps calibration -> skip
                    blk = lambda x: min(4, int((x - ncp) / (n - ncp) * 5))
                    if blk(st) != blk(st + WIN - 1): continue
                    group = f"{r['rec']}#b{blk(st)}"
                elif empty: group = 'calib'
                else: group = r['rec']
                F.append(change_feats(W, prev, relative=not pca)[0])
                M.append(dict(setting=s, rec=r['rec'], presence=int(not empty), calib=calib, group=group,
                              start=st, t_end=(st + WIN) / FS))
    X = np.array(F); M = pd.DataFrame(M)
    for s in SETTINGS:  # fixed 2-min empty-room calibration
        ms = (M.setting == s).values; mc = ms & M.calib.values
        X[ms] = (X[ms] - X[mc].mean(0)) / (X[mc].std(0) + 1e-6)
    return X, M

MODELS = {
    'LR': lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1, class_weight='balanced')),
    'RF': lambda: RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=SEED, class_weight='balanced'),
}
def fit_prob(model, X, y, Xte):
    if model == 'ENS':  # RF+LR probability average
        return 0.5 * (fit_prob('LR', X, y, Xte) + fit_prob('RF', X, y, Xte))
    return MODELS[model]().fit(X, y).predict_proba(Xte)[:, 1]

def splits(M):
    ev = ~M.calib.values; st = M.setting.values; out = []
    for s in SETTINGS:
        ii = np.where(ev & (st == s))[0]
        for a, b in GroupKFold(5).split(ii, groups=M.group.values[ii]): out.append(('by-recording', s, ii[a], ii[b]))
    for s in SETTINGS: out.append(('leave-one-setting-out', f'test={s}', np.where(ev & (st != s))[0], np.where(ev & (st == s))[0]))
    for a, b in [('LOS-BQ', 'NLOS-BQ'), ('LOS-PIFA', 'NLOS-PIFA'), ('NLOS-BQ', 'LOS-BQ'), ('NLOS-PIFA', 'LOS-PIFA'),
                 ('LOS-BQ', 'LOS-PIFA'), ('NLOS-BQ', 'NLOS-PIFA'), ('LOS-PIFA', 'LOS-BQ'), ('NLOS-PIFA', 'NLOS-BQ')]:
        out.append(('cross-pair', f'{a}->{b}', np.where(ev & (st == a))[0], np.where(ev & (st == b))[0]))
    return out

def inner_oof(model, X, y, M, tr):
    """Out-of-fold probabilities on the training set (groups: settings if >1 setting, else recordings)."""
    sets = M.setting.values[tr]
    g = sets if len(np.unique(sets)) > 1 else M.group.values[tr]
    k = min(4, len(np.unique(g))); oof = np.zeros(len(tr))
    for a, b in GroupKFold(k).split(tr, groups=g): oof[b] = fit_prob(model, X[tr[a]], y[tr[a]], X[tr[b]])
    return oof

def oneclass_scores(X, M, te, kind):
    """Anomaly score vs the TEST setting's own 2-min empty calibration windows + threshold from calibration."""
    s = M.setting.values[te[0]]; cal = np.where((M.setting == s).values & M.calib.values)[0]
    C = X[cal]
    if kind == 'maha':
        def d(model, Z): return model.mahalanobis(Z)
        sc = d(LedoitWolf().fit(C), X[te])
        loo = [d(LedoitWolf().fit(np.delete(C, i, 0)), C[i:i + 1])[0] for i in range(len(C))]
        thr = np.max(loo)
    else:
        m = IsolationForest(n_estimators=300, random_state=SEED).fit(C)
        sc = -m.score_samples(X[te]); thr = np.max(-m.score_samples(C))  # in-sample max (optimistic thr)
    return sc, thr

if __name__ == '__main__':
    out = {}
    variants = [('base', 'none', WIN, False), ('hampel', 'hampel', WIN, False), ('hampel+lowpass', 'hampel+lowpass', WIN, False),
                ('movavg', 'movavg', WIN, False), ('ratio', 'ratio', WIN, False), ('hampel+ratio', 'hampel+ratio', WIN, False),
                ('pca(drop1st)', 'none', WIN, True), ('overlap1s', 'none', 100, False)]
    for vname, pre, hop, pca in variants:
        X, M = build(pre, hop, pca); y = M.presence.values
        print(vname, X.shape, 'eval windows', (~M.calib).sum(), flush=True)
        recs_out = []
        for model in ['LR', 'RF', 'ENS']:
            if vname != 'base' and model == 'RF': continue  # RF only for base (LR is the reference)
            for sch, tag, tr, te in splits(M):
                p = fit_prob(model, X[tr], y[tr], X[te])
                d = dict(variant=vname, model=model, scheme=sch, tag=tag, te=te, p=p)
                if vname in ('base', 'overlap1s', 'hampel+ratio', 'ratio') :
                    oof = inner_oof(model, X, y, M, tr); d['thr_fa1'] = np.quantile(oof[y[tr] == 0], 0.99)
                    d['thr_fa3'] = np.quantile(oof[y[tr] == 0], 0.97)
                    cal = np.where((M.setting == M.setting.values[te[0]]).values & M.calib.values)[0]
                    d['thr_calmax'] = fit_prob(model, X[tr], y[tr], X[cal]).max()
                if vname == 'base' and model == 'LR':
                    for kind in ['maha', 'iforest']:
                        d[f'{kind}_sc'], d[f'{kind}_thr'] = oneclass_scores(X, M, te, kind)
                recs_out.append(d)
            print('  ', vname, model, 'done', flush=True)
        out[vname] = dict(M=M, y=y, runs=recs_out)
    pd.to_pickle(out, 'results/fa_runs.pkl')
    print('saved')
