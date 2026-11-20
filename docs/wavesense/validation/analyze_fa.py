"""Post-processing (thresholds, k-of-n, hysteresis, voting, one-class fusion) + metrics + bootstrap CIs + charts."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, precision_recall_curve, auc
R = pd.read_pickle('results/fa_runs.pkl'); rng = np.random.default_rng(0)

def segments(M, te):
    """Yield arrays of positions (into te) per continuous segment (same recording, consecutive starts)."""
    rec, st = M.rec.values[te], M.start.values[te]
    hop = np.diff(np.sort(np.unique(M.start.values)))[:1]
    order = np.lexsort((st, rec)); segs, cur = [], [order[0]]
    for a, b in zip(order[:-1], order[1:]):
        if rec[a] == rec[b] and st[b] - st[a] <= HOP[0]: cur.append(b)
        else: segs.append(np.array(cur)); cur = [b]
    segs.append(np.array(cur)); return segs

def kofn(x, k, n):  # causal: declare presence if >=k of the last n binary decisions are positive
    c = np.cumsum(np.concatenate([[0], x.astype(int)])); i = np.arange(1, len(x) + 1)
    return (c[i] - c[np.maximum(0, i - n)]) >= k
def hyst(p, on, off):
    s, out = False, np.zeros(len(p), bool)
    for i, v in enumerate(p):
        s = (v > on) if not s else (v >= off); out[i] = s
    return out

def apply(run, M, rule):
    te, p = run['te'], run['p']; dec = np.zeros(len(te), bool)
    kind = rule[0]
    if kind in ('and', 'andkofn'):  # classifier AND one-class anomaly
        base = p > 0.5; an = run[f'{rule[1]}_sc'] > run[f'{rule[1]}_thr']; raw = base & an
    elif kind in ('oc', 'ockofn'):
        raw = run[f'{rule[1]}_sc'] > run[f'{rule[1]}_thr']
    else:
        t = rule[1] if not isinstance(rule[1], str) else run[rule[1]]; raw = p > t
    for seg in segments(M, te):
        if kind in ('thr', 'and', 'oc'): dec[seg] = raw[seg]
        elif kind in ('kofn', 'andkofn', 'ockofn'): dec[seg] = kofn(raw[seg], rule[2], rule[3])
        elif kind == 'meanlast':  # mean prob of last n windows > t
            q = p[seg]; c = np.cumsum(np.concatenate([[0], q])); i = np.arange(1, len(q) + 1); n = rule[2]
            dec[seg] = (c[i] - c[np.maximum(0, i - n)]) / np.minimum(i, n) > t
        elif kind == 'hyst': dec[seg] = hyst(p[seg], rule[1], rule[2])
    return dec

def latency(M, te, dec):
    """Per person recording: seconds from its first evaluated window to first positive decision (recording start
    stands in for 'person appears' - artificial). Never detected -> counted separately."""
    lat, never = [], 0
    for r in np.unique(M.rec.values[te][M.presence.values[te] == 1]):
        m = M.rec.values[te] == r; t = M.t_end.values[te][m]; d = dec[m]; o = np.argsort(t); t, d = t[o], d[o]
        if d.any(): lat.append(t[np.argmax(d)] - t[0])
        else: never += 1
    return lat, never

def metr(y, d):
    fa = d[y == 0].mean(); miss = 1 - d[y == 1].mean(); return dict(bal_acc=1 - (fa + miss) / 2, FA=fa, miss=miss)

def evaluate(variant, model, rule, name, family):
    D = R[variant]; M, y = D['M'], D['y']; rows, units = [], []
    for run in D['runs']:
        if run['model'] != model: continue
        dec = apply(run, M, rule); te = run['te']; yt = y[te]
        lat, never = latency(M, te, dec)
        rows.append(dict(scheme=run['scheme'], tag=run['tag'], **metr(yt, dec), lat=lat, never=never, nrec=len(lat) + never))
        units.append((run['scheme'], run['tag'], M.group.values[te], yt, dec))
    out = []
    for sch in ['by-recording', 'leave-one-setting-out', 'cross-pair']:
        rs = [r for r in rows if r['scheme'] == sch]; us = [u for u in units if u[0] == sch]
        if sch == 'by-recording':  # aggregate folds per setting first
            yy = np.concatenate([u[3] for u in us]); dd = np.concatenate([u[4] for u in us])
        lat = sum([r['lat'] for r in rs], []); never = sum(r['never'] for r in rs); nrec = sum(r['nrec'] for r in rs)
        # pooled metrics over all test windows of the scheme + block bootstrap over (tag, group) units
        Y = np.concatenate([u[3] for u in us]); Dd = np.concatenate([u[4] for u in us])
        U = np.concatenate([[f'{u[1]}|{g}' for g in u[2]] for u in us]); uu, inv = np.unique(U, return_inverse=True)
        pos = [np.where(inv == i)[0] for i in range(len(uu))]
        bs = []
        for _ in range(500):
            ii = np.concatenate([pos[j] for j in rng.integers(0, len(uu), len(uu))]); bs.append(list(metr(Y[ii], Dd[ii]).values()))
        bs = np.array(bs); lo, hi = np.nanpercentile(bs, 2.5, 0), np.nanpercentile(bs, 97.5, 0)
        m = metr(Y, Dd)
        out.append(dict(family=family, method=name, scheme=sch, **m, bal_lo=lo[0], bal_hi=hi[0], FA_lo=lo[1], FA_hi=hi[1],
                        miss_lo=lo[2], miss_hi=hi[2], lat_median_s=np.median(lat) if lat else np.nan,
                        lat_p90_s=np.percentile(lat, 90) if lat else np.nan, recs_never_detected=f'{never}/{nrec}',
                        _Y=Y, _D=Dd, _U=U))
    return out

HOP = [400]
METHODS = [  # (variant, model, rule, name, family)
    ('base', 'LR', ('thr', 0.5), 'BASE: chg+fixed-calib LR @0.5', '0 baseline'),
    ('base', 'RF', ('thr', 0.5), 'RF @0.5', '6 ensemble'),
    ('base', 'ENS', ('thr', 0.5), 'RF+LR avg @0.5', '6 ensemble'),
    ('base', 'LR', ('kofn', 0.5, 2, 3), 'LR 2-of-3', '1 smoothing'),
    ('base', 'LR', ('kofn', 0.5, 3, 5), 'LR 3-of-5', '1 smoothing'),
    ('base', 'LR', ('kofn', 0.5, 2, 2), 'LR 2-of-2', '1 smoothing'),
    ('base', 'LR', ('hyst', 0.7, 0.3), 'LR hysteresis on.7/off.3', '1 smoothing'),
    ('base', 'LR', ('hyst', 0.9, 0.5), 'LR hysteresis on.9/off.5', '1 smoothing'),
    ('base', 'LR', ('thr', 'thr_fa3'), 'LR thr for FA<=3% (train OOF)', '2 threshold'),
    ('base', 'LR', ('thr', 'thr_fa1'), 'LR thr for FA<=1% (train OOF)', '2 threshold'),
    ('base', 'LR', ('thr', 'thr_calmax'), 'LR thr=max on test calib', '2 threshold'),
    ('hampel', 'LR', ('thr', 0.5), 'Hampel', '4 denoise'),
    ('hampel+lowpass', 'LR', ('thr', 0.5), 'Hampel+Butterworth 10Hz', '4 denoise'),
    ('movavg', 'LR', ('thr', 0.5), 'moving average 0.1s', '4 denoise'),
    ('ratio', 'LR', ('thr', 0.5), 'adjacent-subcarrier ratio', '4 denoise'),
    ('hampel+ratio', 'LR', ('thr', 0.5), 'Hampel+ratio', '4 denoise'),
    ('pca(drop1st)', 'LR', ('thr', 0.5), 'PCA drop 1st, keep 5', '4 denoise'),
    ('base', 'LR', ('oc', 'maha'), 'Mahalanobis(calib) alone', '5 one-class'),
    ('base', 'LR', ('oc', 'iforest'), 'IsolationForest(calib) alone', '5 one-class'),
    ('base', 'LR', ('and', 'maha'), 'LR AND Mahalanobis', '5 one-class'),
    ('base', 'LR', ('and', 'iforest'), 'LR AND IsolationForest', '5 one-class'),
]
METHODS_OV = [
    ('overlap1s', 'LR', ('thr', 0.5), 'overlap 4s/1s hop, per-window', '3 overlap'),
    ('overlap1s', 'LR', ('kofn', 0.5, 3, 4), 'overlap + vote 3-of-4', '3 overlap'),
    ('overlap1s', 'LR', ('kofn', 0.5, 3, 5), 'overlap + vote 3-of-5', '3 overlap'),
    ('overlap1s', 'LR', ('meanlast', 0.5, 4), 'overlap + mean prob last 4', '3 overlap'),
]
COMBOS = [  # chosen AFTER seeing component results -> selection bias, flagged in report
    ('base', 'ENS', ('kofn', 0.5, 2, 3), 'C1 RF+LR avg + 2-of-3', '7 combo'),
    ('base', 'ENS', ('thr', 'thr_fa3'), 'C2 RF+LR avg + thr FA<=3%', '7 combo'),
    ('base', 'ENS', ('kofn', 'thr_fa3', 2, 3), 'C3 RF+LR avg + thr FA<=3% + 2-of-3', '7 combo'),
    ('base', 'LR', ('kofn', 'thr_fa3', 2, 3), 'C4 LR thr FA<=3% + 2-of-3', '7 combo'),
    ('overlap1s', 'ENS', ('kofn', 0.5, 3, 5), 'C5 overlap + RF+LR avg + vote 3-of-5', '7 combo'),
    ('overlap1s', 'ENS', ('kofn', 'thr_fa3', 3, 5), 'C6 overlap + RF+LR avg + thr FA<=3% + 3-of-5', '7 combo'),
    ('ratio', 'ENS', ('kofn', 0.5, 2, 3), 'C7 ratio + RF+LR avg + 2-of-3', '7 combo'),
    ('base', 'LR', ('andkofn', 'maha', 2, 3), 'C8 LR AND Mahalanobis + 2-of-3', '7 combo'),
    ('base', 'LR', ('ockofn', 'maha', 2, 3), 'C9 Mahalanobis alone + 2-of-3 (no training)', '7 combo'),
    ('base', 'LR', ('ockofn', 'maha', 3, 5), 'C10 Mahalanobis alone + 3-of-5 (no training)', '7 combo'),
]
res = []
for m in METHODS + COMBOS[:4] + COMBOS[6:]:
    HOP[0] = 400; res += evaluate(*m)
for m in METHODS_OV + COMBOS[4:6]:
    HOP[0] = 100; res += evaluate(*m)
df = pd.DataFrame(res)
pub = df.drop(columns=['_Y', '_D', '_U'])
pub.to_csv('results/fa_results.csv', index=False)
pd.set_option('display.width', 260); pd.set_option('display.max_colwidth', 48)
for sch in ['by-recording', 'leave-one-setting-out', 'cross-pair']:
    print('\n==', sch); print(pub[pub.scheme == sch][['family', 'method', 'bal_acc', 'FA', 'FA_lo', 'FA_hi', 'miss', 'miss_lo', 'miss_hi', 'bal_lo', 'bal_hi', 'lat_median_s', 'lat_p90_s', 'recs_never_detected']].round(3).to_string(index=False))

# paired bootstrap vs BASE (same windows only)
base = {r['scheme']: r for r in res if r['method'].startswith('BASE')}
pair = []
for r in res:
    b = base[r['scheme']]
    if len(r['_Y']) != len(b['_Y']) or (r['_U'] != b['_U']).any() or r['method'].startswith('BASE'): continue
    uu, inv = np.unique(r['_U'], return_inverse=True); pos = [np.where(inv == i)[0] for i in range(len(uu))]; dd = []
    for _ in range(500):
        ii = np.concatenate([pos[j] for j in rng.integers(0, len(uu), len(uu))])
        a, c = metr(r['_Y'][ii], r['_D'][ii]), metr(b['_Y'][ii], b['_D'][ii]); dd.append([a[k] - c[k] for k in ['bal_acc', 'FA', 'miss']])
    dd = np.array(dd); lo, hi = np.percentile(dd, 2.5, 0), np.percentile(dd, 97.5, 0)
    a, c = metr(r['_Y'], r['_D']), metr(b['_Y'], b['_D'])
    pair.append(dict(method=r['method'], scheme=r['scheme'], d_bal=a['bal_acc'] - c['bal_acc'], d_bal_lo=lo[0], d_bal_hi=hi[0],
                     d_FA=a['FA'] - c['FA'], d_FA_lo=lo[1], d_FA_hi=hi[1], d_miss=a['miss'] - c['miss'], d_miss_lo=lo[2], d_miss_hi=hi[2]))
P = pd.DataFrame(pair); P.to_csv('results/fa_paired_vs_base.csv', index=False)
print('\n== paired difference vs BASE (95% block-bootstrap CI)'); print(P.round(3).to_string(index=False))

# ---------------- charts ----------------
# ROC / PR (leave-one-setting-out, pooled probabilities)
fig, ax = plt.subplots(1, 2, figsize=(13, 5))
def pooled(variant, model, key='p'):
    D = R[variant]; y = D['y']; ys, ps = [], []
    for run in D['runs']:
        if run['model'] == model and run['scheme'] == 'leave-one-setting-out': ys.append(y[run['te']]); ps.append(run[key])
    return np.concatenate(ys), np.concatenate(ps)
for (v, mdl, key, lab) in [('base', 'LR', 'p', 'BASE LR'), ('base', 'RF', 'p', 'RF'), ('base', 'ENS', 'p', 'RF+LR avg'),
                           ('ratio', 'LR', 'p', 'ratio LR'), ('hampel', 'LR', 'p', 'Hampel LR'), ('pca(drop1st)', 'LR', 'p', 'PCA LR'),
                           ('overlap1s', 'LR', 'p', 'overlap LR (per window)'), ('base', 'LR', 'maha_sc', 'Mahalanobis'), ('base', 'LR', 'iforest_sc', 'IsolationForest')]:
    yy, pp = pooled(v, mdl, key); f, t, _ = roc_curve(yy, pp); pr, rc, _ = precision_recall_curve(yy, pp)
    ax[0].plot(f, t, label=f'{lab} (AUC {auc(f, t):.3f})'); ax[1].plot(rc, pr, label=lab)
for x in [0.01, 0.03]: ax[0].axvline(x, ls=':', c='gray')
ax[0].set_xscale('symlog', linthresh=0.01); ax[0].set_xlim(0, 1); ax[0].set_xlabel('false-alarm rate (log above 1%)'); ax[0].set_ylabel('detection rate (1 - miss)')
ax[0].set_title('ROC, presence, unseen setting (leave-one-setting-out, pooled)', fontsize=10); ax[0].legend(fontsize=7)
ax[1].set_xlabel('recall (detection rate)'); ax[1].set_ylabel('precision'); ax[1].set_title('Precision-recall, same', fontsize=10); ax[1].legend(fontsize=7)
plt.tight_layout(); plt.savefig('results/fig6_fa_roc_pr.png', dpi=150); plt.close()

# FA vs miss scatter per scheme
fig, ax = plt.subplots(1, 3, figsize=(20, 6.5))
fams = sorted(pub.family.unique()); cm = plt.get_cmap('tab10')
for k, sch in enumerate(['by-recording', 'leave-one-setting-out', 'cross-pair']):
    s = pub[pub.scheme == sch]
    s = s[s.method.str.match(r'BASE|RF\+LR avg @|LR 2-of-3|LR 3-of-5|LR hysteresis on.7|LR thr for FA<=1|LR thr=max|Hampel$|PCA|Mahalanobis\(|LR AND Mahalanobis$|overlap \+ vote 3-of-5|C1 |C4 |C8 |C9 |C10 ')]
    for i, f in enumerate(fams):
        q = s[s.family == f]; ax[k].scatter(q.FA, q.miss, color=cm(i), label=f, s=30)
        for _, r in q.iterrows(): ax[k].annotate(r.method.split(':')[0].replace(' (no training)','')[:34], (r.FA, r.miss), fontsize=7)
    ax[k].set_xlabel('false-alarm rate'); ax[k].set_ylabel('miss rate'); ax[k].set_title(sch + ' (ratio / IsolationForest variants omitted: far off-scale)', fontsize=9); ax[k].grid(alpha=.3)
ax[0].legend(fontsize=7)
plt.tight_layout(); plt.savefig('results/fig7_fa_vs_miss.png', dpi=150); plt.close()
print('charts done')
