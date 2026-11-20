"""Baseline-drift fixes on Wallhack1.8k presence:
 (1) auto-updating empty-room baseline (EMA, updated only when a label-free low-motion gate says 'empty'; frozen otherwise)
 (2) change-based features (std/var, first-difference energy, change vs previous window) instead of absolute levels
 and (1)+(2). Compared with no calibration and a fixed 2-min initial calibration.
Streams are simulated per setting in time order. ARTIFICIAL: there is only one empty recording per setting, so the stream is
  [first 20% of b1 = calibration] + 10x( next b1 chunk , one person recording )  -- person recordings are separate sessions
  spliced in; real transitions (person enters/leaves) never occur in the data."""
import json, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold
from sklearn.metrics import balanced_accuracy_score
from load_wallhack import recordings, load_file
from features import valid_subcarriers, windows, feat_raw, _entropy

SEED = 0; CAL = 0.2; ALPHA = 0.05; K = 3.0; NCHUNK = 10
recs = recordings(); amps = {r['rec']: load_file(r['path'])[0] for r in recs}
V = valid_subcarriers(np.concatenate(list(amps.values())))
SETTINGS = ['LOS-BQ', 'LOS-PIFA', 'NLOS-BQ', 'NLOS-PIFA']

def feat_change(W, prev_mean):
    """W:(n,T,S). prev_mean:(n,S) mean amplitude of previous window in the same recording."""
    D = W - W.mean(1, keepdims=True)
    std = D.std(1); var = std ** 2; de = (np.diff(W, axis=1) ** 2).mean(1)
    pd_ = np.abs(W.mean(1) - prev_mean) / (prev_mean + 1e-6)
    agg = np.stack([std.mean(1), var.mean(1), de.mean(1), pd_.mean(1),
                    np.array([_entropy((d / (d.std() + 1e-9)).ravel()) for d in D])], 1)
    return np.concatenate([std, var, de, pd_, agg], 1)

def motion_score(W):
    return (W / (W.mean(1, keepdims=True) + 1e-6)).std(1).mean(1)

# ---- build per-setting streams ----
rows = []
for s in SETTINGS:
    scen, sysm = s.split('-')
    rs = [r for r in recs if r['scen'] == scen and r['sys'] == sysm]
    b = [r for r in rs if r['act'] == 0][0]; ppl = [r for r in rs if r['act'] > 0]
    def wins(r):
        W = windows(amps[r['rec']][:, V]); m = W.mean(1)
        prev = np.vstack([m[:1], m[:-1]])
        return W[1:], prev[1:]  # drop first window of each recording (no previous window)
    Wb, Pb = wins(b); ncal = int(round(len(Wb) * CAL))
    parts = [(Wb[:ncal], Pb[:ncal], dict(rec=b['rec'], presence=0, calib=True, btime=np.arange(ncal)))]
    chunks = np.array_split(np.arange(ncal, len(Wb)), NCHUNK)
    for i in range(NCHUNK):
        c = chunks[i]
        parts.append((Wb[c], Pb[c], dict(rec=b['rec'], presence=0, calib=False, btime=c)))
        Wp, Pp = wins(ppl[i]); parts.append((Wp, Pp, dict(rec=ppl[i]['rec'], presence=1, calib=False, btime=np.full(len(Wp), -1))))
    for Wx, Px, m in parts:
        fa, fc, ms = feat_raw(Wx), feat_change(Wx, Px), motion_score(Wx)
        for j in range(len(Wx)):
            rows.append(dict(setting=s, rec=m['rec'], presence=m['presence'], calib=m['calib'],
                             btime=int(m['btime'][j]), nb=len(Wb), fa=fa[j], fc=fc[j], score=ms[j]))
df = pd.DataFrame(rows); df['t'] = df.groupby('setting').cumcount()
# empty-recording time position (0..1) after calibration, for drift check
df['bpos'] = np.where(df.btime >= 0, df.btime / df.nb, np.nan)
FEATS = {'abs': np.stack(df.fa.values), 'chg': np.stack(df.fc.values)}
score = df.score.values
print('windows', len(df), df[~df.calib].groupby(['setting', 'presence']).size().unstack().to_dict())

def baseline_norm(X, mode, alpha=ALPHA, k=K):
    """Causal per-setting normalization. Returns normalized X and the gate/threshold-detector decision (1=person)."""
    Z = np.zeros_like(X, dtype=np.float64); det = np.zeros(len(X), int); upd = np.zeros(len(X), bool)
    for s in SETTINGS:
        ii = np.where((df.setting == s).values)[0]  # already in stream order
        cal = ii[df.calib.values[ii]]
        mu, var = X[cal].mean(0), X[cal].var(0) + 1e-6
        ms, vs = score[cal].mean(), score[cal].var() + 1e-12
        gate0 = ms + k * np.sqrt(vs); below = []  # fixed gate from the initial calibration (used by ema_safe)
        for t in ii:
            x = X[t]
            if mode == 'none':
                Z[t] = x
            else:
                Z[t] = (x - mu) / np.sqrt(var)
            person = score[t] > ms + k * np.sqrt(vs); det[t] = int(person)
            below.append(score[t] < gate0)
            if mode == 'ema':
                ok = not person                      # naive: adaptive gate says empty
            elif mode == 'ema_safe':
                ok = len(below) >= 3 and all(below[-3:])  # fixed initial gate + 12 s hold-off (3 windows) before updating
            else:
                ok = False
            if ok and not df.calib.values[t]:
                upd[t] = True
                d = x - mu; mu = mu + alpha * d; var = (1 - alpha) * (var + alpha * d * d)
                ds = score[t] - ms; ms = ms + alpha * ds; vs = (1 - alpha) * (vs + alpha * ds * ds)
    return Z, det, upd

MODELS = {
    'RF': lambda: RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=SEED, class_weight='balanced'),
    'LR': lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1, class_weight='balanced')),
}
METHODS = {  # name: (feature, baseline mode)
    'abs / no-calib': ('abs', 'none'), 'abs / fixed-calib': ('abs', 'fixed'), 'abs / EMA (fix1)': ('abs', 'ema'),
    'chg (fix2) / no-calib': ('chg', 'none'), 'chg / fixed-calib': ('chg', 'fixed'), 'chg + EMA (fix1+2)': ('chg', 'ema'),
    'abs / EMA-safe': ('abs', 'ema_safe'), 'chg + EMA-safe': ('chg', 'ema_safe'),
}
y = df.presence.values; ev = ~df.calib.values; st = df.setting.values
grp = np.where(y == 1, df.rec.values, [f'{r}#b{int(p * 5 // 1)}' if p == p else r for r, p in zip(df.rec.values, (df.bpos.values - CAL) / (1 - CAL))])
grp = np.array([g.replace('#b5', '#b4') for g in grp])

def metrics(yt, p, bpos):
    e = yt == 0; fa = p[e].mean()
    bp = bpos[e]; mid = (CAL + 1) / 2
    return dict(bal_acc=balanced_accuracy_score(yt, p), false_alarm=fa, miss=1 - p[yt == 1].mean(),
                fa_early=p[e][bp < mid].mean(), fa_late=p[e][bp >= mid].mean())

def splits(scheme):
    out = []
    if scheme == 'group-by-recording (within setting)':
        for s in SETTINGS:
            ii = np.where(ev & (st == s))[0]
            for a, b in GroupKFold(5).split(ii, groups=grp[ii]): out.append((s, ii[a], ii[b]))
    elif scheme == 'leave-one-setting-out':
        for s in SETTINGS: out.append((f'test={s}', np.where(ev & (st != s))[0], np.where(ev & (st == s))[0]))
    else:
        for a, b in [('LOS-BQ', 'NLOS-BQ'), ('LOS-PIFA', 'NLOS-PIFA'), ('NLOS-BQ', 'LOS-BQ'), ('NLOS-PIFA', 'LOS-PIFA'),
                     ('LOS-BQ', 'LOS-PIFA'), ('NLOS-BQ', 'NLOS-PIFA'), ('LOS-PIFA', 'LOS-BQ'), ('NLOS-PIFA', 'NLOS-BQ')]:
            out.append((f'{a}->{b}', np.where(ev & (st == a))[0], np.where(ev & (st == b))[0]))
    return out

SCHEMES = ['group-by-recording (within setting)', 'leave-one-setting-out', 'cross-pair']
res, preds = [], {}
bpos = df.bpos.values
for mname_, (fk, mode) in METHODS.items():
    Z, _, upd = baseline_norm(FEATS[fk], mode)
    if mode.startswith('ema'): print(f'  [{mname_}] person windows absorbed into baseline: {upd[ev & (y == 1)].mean():.3f}; empty windows used for update: {upd[ev & (y == 0)].mean():.3f}')
    for sch in SCHEMES:
        for mdl, mk in MODELS.items():
            P = np.full(len(df), -1); per = []
            for tag, tr, te in splits(sch):
                p = mk().fit(Z[tr], y[tr]).predict(Z[te])
                if sch == 'group-by-recording (within setting)': P[te] = p
                else: per.append(dict(tag=tag, **metrics(y[te], p, bpos[te])))
                if sch == 'leave-one-setting-out': P[te] = p
            if sch == 'group-by-recording (within setting)':
                per = [dict(tag=s, **metrics(y[ev & (st == s)], P[ev & (st == s)], bpos[ev & (st == s)])) for s in SETTINGS]
            preds[(mname_, sch, mdl)] = P
            for r in per: res.append(dict(method=mname_, scheme=sch, model=mdl, **r))
            m = pd.DataFrame(per).mean(numeric_only=True)
            print(f'{mname_:22s} {sch:38s} {mdl} bal={m.bal_acc:.3f} FA={m.false_alarm:.3f} FAearly={m.fa_early:.3f} FAlate={m.fa_late:.3f}', flush=True)

# ---- training-free threshold detector (motion score vs baseline) ----
for mode, name in [('fixed', 'threshold / fixed-calib'), ('ema', 'threshold / EMA (fix1)'), ('ema_safe', 'threshold / EMA-safe')]:
    _, det, upd = baseline_norm(FEATS['chg'][:, :1], mode)
    for s in SETTINGS:
        m = ev & (st == s)
        for sch in SCHEMES[:2]:  # no training -> identical in every scheme; listed under both for the table
            res.append(dict(method=name, scheme=sch, model='-', tag=s if sch.startswith('group') else f'test={s}', **metrics(y[m], det[m], bpos[m])))
    preds[(name, 'all', '-')] = det
    print(name, pd.DataFrame([r for r in res if r['method'] == name and r['scheme'].startswith('group')]).mean(numeric_only=True).round(3).to_dict())
# no-calib threshold: learn a single global threshold on the training settings (LOSO)
det = np.full(len(df), -1)
for s in SETTINGS:
    tr = ev & (st != s); te = ev & (st == s)
    cands = np.quantile(score[tr], np.linspace(0.01, 0.99, 197))
    thr = max(cands, key=lambda c: balanced_accuracy_score(y[tr], (score[tr] > c).astype(int)))
    det[te] = (score[te] > thr).astype(int)
    res.append(dict(method='threshold / no-calib (global thr)', scheme='leave-one-setting-out', model='-', tag=f'test={s}', **metrics(y[te], det[te], bpos[te])))
preds[('threshold / no-calib (global thr)', 'leave-one-setting-out', '-')] = det

# ---- alpha / k sensitivity for the EMA threshold detector (reported, NOT used to pick the main setting) ----
sens = []
for a in [0.01, 0.02, 0.05, 0.1, 0.2]:
    for k in [2.0, 3.0, 4.0]:
        for mode in ['fixed', 'ema', 'ema_safe']:
            _, det, _ = baseline_norm(FEATS['chg'][:, :1], mode, alpha=a, k=k)
            mm = [metrics(y[ev & (st == s)], det[ev & (st == s)], bpos[ev & (st == s)]) for s in SETTINGS]
            sens.append(dict(alpha=a, k=k, mode=mode, **pd.DataFrame(mm).mean().to_dict()))
pd.DataFrame(sens).drop_duplicates(['k', 'mode', 'bal_acc', 'false_alarm']).to_csv('results/drift_threshold_sensitivity.csv', index=False)

R = pd.DataFrame(res); R.to_csv('results/drift_results.csv', index=False)
np.save('results/drift_preds.npy', {'|'.join(k): v for k, v in preds.items()}, allow_pickle=True)
df[['setting', 'rec', 'presence', 'calib', 'btime', 'bpos', 't', 'score']].to_csv('results/drift_stream_meta.csv', index=False)
print(R.groupby(['scheme', 'method', 'model'])[['bal_acc', 'false_alarm', 'miss', 'fa_early', 'fa_late']].mean().round(3).to_string())
