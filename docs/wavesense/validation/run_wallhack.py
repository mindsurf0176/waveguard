"""WaveSense pipeline reproduction on Wallhack1.8k raw ESP32 CSI.
Every number in results comes from this script (results/wallhack_results.csv)."""
import itertools, json, os, sys, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold, GroupKFold
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
from load_wallhack import recordings, load_file
from features import valid_subcarriers, windows, FEATS, augment

SEED = 0
OUT = 'results'; os.makedirs(OUT, exist_ok=True)
CALIB_FRAC = 0.2  # first 20% of each empty-room recording = install-time calibration, never evaluated

# ---------------- data ----------------
recs = recordings()
amps = {r['rec']: load_file(r['path'])[0] for r in recs}
VALID = valid_subcarriers(np.concatenate(list(amps.values())))
L_LTF = VALID[VALID < 64]; HT_LTF = VALID[VALID >= 64]
print('valid subcarriers:', len(VALID), 'L-LTF', len(L_LTF), 'HT-LTF', len(HT_LTF))

Ws, meta = [], []
for r in recs:
    W = windows(amps[r['rec']][:, VALID])
    n = len(W)
    for i in range(n):
        m = dict(scen=r['scen'], sys=r['sys'], setting=f"{r['scen']}-{r['sys']}", rec=r['rec'],
                 act=r['act'], room=r['room'], idx=i, calib=False, group=r['rec'])
        if r['act'] == 0:
            ncal = int(round(n * CALIB_FRAC))
            m['calib'] = i < ncal
            # empty room is a single 10-min recording per setting -> split remaining into 5 contiguous blocks
            m['group'] = f"{r['rec']}#blk{min(4, int((i - ncal) / max(1, (n - ncal)) * 5))}"
        meta.append(m)
    Ws.append(W)
W_all = np.concatenate(Ws).astype(np.float32); meta = pd.DataFrame(meta)
meta['presence'] = (meta.act > 0).astype(int)
print('windows:', len(meta), '| calib windows (excluded from eval):', meta.calib.sum())
print(meta[~meta.calib].groupby(['setting', 'act']).size().unstack())

SUBC = {'all': np.arange(len(VALID)), 'L-LTF': np.arange(len(L_LTF)), 'HT-LTF': np.arange(len(L_LTF), len(VALID))}
_fcache = {}
def feats(name, subc):
    k = (name, subc)
    if k not in _fcache:
        _fcache[k] = FEATS[name](W_all[:, :, SUBC[subc]])
    return _fcache[k]

def normalize(X, norm):
    X = X.copy()
    if norm == 'calib':  # z-score with this setting's empty-room calibration windows (deployable)
        for s in meta.setting.unique():
            ms = (meta.setting == s).values; mc = ms & meta.calib.values
            mu, sd = X[mc].mean(0), X[mc].std(0) + 1e-6
            X[ms] = (X[ms] - mu) / sd
    elif norm == 'perrec':  # z-score each recording with its own stats (needs whole test recording; leaky/destructive)
        for g in meta.rec.unique():
            mg = (meta.rec == g).values
            X[mg] = (X[mg] - X[mg].mean(0)) / (X[mg].std(0) + 1e-6)
    return X

MODELS = {
    'RF': lambda: RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=SEED, class_weight='balanced'),
    'LR': lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1, class_weight='balanced')),
}

CONFIGS = {  # name: (feature set, normalization, subcarriers, augmentation)
    'A_raw':          ('raw', 'none', 'all', False),   # poster pipeline as written
    'B_dyn(static-removed)': ('dyn', 'none', 'all', False),
    'C_rel(gain-norm)':      ('rel', 'none', 'all', False),
    'D_raw+calib':    ('raw', 'calib', 'all', False),
    'E_rel+calib':    ('rel', 'calib', 'all', False),
    'F_raw+perrec':   ('raw', 'perrec', 'all', False),
    'G_raw+aug':      ('raw', 'none', 'all', True),
    'H_rel+aug':      ('rel', 'none', 'all', True),
    'I_rel_L-LTF':    ('rel', 'none', 'L-LTF', False),
    'J_rel_HT-LTF':   ('rel', 'none', 'HT-LTF', False),
}

rows, cms = [], {}
def run(task, scheme, label_col, mask, splits, cfgs, tag=''):
    y_all = meta[label_col].values
    for cname in cfgs:
        fname, norm, subc, aug = CONFIGS[cname]
        X = normalize(feats(fname, subc), norm)
        for mname, mk in MODELS.items():
            ys, ps = [], []
            accs, baccs, majs = [], [], []
            for tr, te in splits:
                Xtr, ytr = X[tr], y_all[tr]
                if aug:
                    rng = np.random.default_rng(SEED)
                    Wa = augment(W_all[tr][:, :, SUBC[subc]], rng)
                    Xtr = np.concatenate([Xtr, FEATS[fname](Wa)]); ytr = np.concatenate([ytr, np.tile(ytr, 2)])
                mdl = mk(); mdl.fit(Xtr, ytr); p = mdl.predict(X[te])
                ys.append(y_all[te]); ps.append(p)
                accs.append(accuracy_score(y_all[te], p)); baccs.append(balanced_accuracy_score(y_all[te], p))
                vals, cnt = np.unique(y_all[te], return_counts=True); majs.append(cnt.max() / cnt.sum())
            yc, pc = np.concatenate(ys), np.concatenate(ps)
            rows.append(dict(task=task, scheme=scheme, tag=tag, config=cname, model=mname, folds=len(splits),
                             n_test=len(yc), acc=np.mean(accs), bal_acc=np.mean(baccs),
                             pooled_acc=accuracy_score(yc, pc), majority_baseline=np.mean(majs),
                             classes=json.dumps({int(k): int(v) for k, v in zip(*np.unique(yc, return_counts=True))})))
            labs = sorted(np.unique(y_all[mask]))
            cms[(task, scheme, tag, cname, mname)] = ([int(v) for v in labs], confusion_matrix(yc, pc, labels=labs).tolist())
            print(f"{task:9s} {scheme:28s} {tag:22s} {cname:22s} {mname} acc={np.mean(accs):.3f} bal={np.mean(baccs):.3f} maj={np.mean(majs):.3f}", flush=True)

def idx(m): return np.where(m)[0]
def random_splits(mask, y, k=5):
    ii = idx(mask); skf = StratifiedKFold(k, shuffle=True, random_state=SEED)
    return [(ii[a], ii[b]) for a, b in skf.split(ii, y[ii])]
def group_splits(mask, groups, k):
    ii = idx(mask); gkf = GroupKFold(k)
    return [(ii[a], ii[b]) for a, b in gkf.split(ii, groups=groups[ii])]

ALL = list(CONFIGS)

def main():
    ev = ~meta.calib.values
    G = meta.group.values

    # ---------- Task 1: presence (empty vs person) ----------
    y = meta.presence.values
    for s in sorted(meta.setting.unique()):
        m = ev & (meta.setting == s).values
        run('presence', '1_random-window-5fold', 'presence', m, random_splits(m, y), ALL, s)
        run('presence', '2_group-by-recording-5fold', 'presence', m, group_splits(m, G, 5), ALL, s)
    # cross-environment
    settings = sorted(meta.setting.unique())
    for te_s in settings:  # leave-one-setting-out
        tr = idx(ev & (meta.setting != te_s).values); te = idx(ev & (meta.setting == te_s).values)
        run('presence', '3_leave-one-setting-out', 'presence', ev, [(tr, te)], ALL, f'test={te_s}')
    for a, b in [('LOS-BQ', 'NLOS-BQ'), ('LOS-PIFA', 'NLOS-PIFA'), ('NLOS-BQ', 'LOS-BQ'), ('NLOS-PIFA', 'LOS-PIFA'),
                 ('LOS-BQ', 'LOS-PIFA'), ('NLOS-BQ', 'NLOS-PIFA'), ('LOS-PIFA', 'LOS-BQ'), ('NLOS-PIFA', 'NLOS-BQ')]:
        tr = idx(ev & (meta.setting == a).values); te = idx(ev & (meta.setting == b).values)
        run('presence', '4_cross-pair', 'presence', ev, [(tr, te)], ALL, f'{a}->{b}')

    # ---------- Task 2: location (room/position 1-5, person windows only) ----------
    y = meta.room.values
    actg = meta.act.astype(str).values  # w vs ww recordings of the same room
    for s in settings:
        m = ev & (meta.setting == s).values & (meta.act > 0).values
        run('location', '1_random-window-5fold', 'room', m, random_splits(m, y), ALL, s)
        run('location', '2_group-by-recording(w|ww)', 'room', m, group_splits(m, actg, 2), ALL, s)
    for a, b in [('NLOS-BQ', 'NLOS-PIFA'), ('NLOS-PIFA', 'NLOS-BQ'), ('LOS-BQ', 'LOS-PIFA'), ('LOS-PIFA', 'LOS-BQ')]:
        tr = idx(ev & (meta.setting == a).values & (meta.act > 0).values)
        te = idx(ev & (meta.setting == b).values & (meta.act > 0).values)
        run('location', '4_cross-pair(system)', 'room', ev & (meta.act > 0).values, [(tr, te)], ALL, f'{a}->{b}')

    # ---------- Task 3: activity (empty / walk / walk+wave) ----------
    y = meta.act.values
    for s in settings:
        m = ev & (meta.setting == s).values
        run('activity', '1_random-window-5fold', 'act', m, random_splits(m, y), ['A_raw', 'C_rel(gain-norm)', 'E_rel+calib'], s)
        run('activity', '2_group-by-recording-5fold', 'act', m, group_splits(m, G, 5), ['A_raw', 'C_rel(gain-norm)', 'E_rel+calib'], s)
    for te_s in settings:
        tr = idx(ev & (meta.setting != te_s).values); te = idx(ev & (meta.setting == te_s).values)
        run('activity', '3_leave-one-setting-out', 'act', ev, [(tr, te)], ['A_raw', 'C_rel(gain-norm)', 'E_rel+calib'], f'test={te_s}')

    df = pd.DataFrame(rows); df.to_csv(f'{OUT}/wallhack_results.csv', index=False)
    json.dump({'|'.join(k): v for k, v in cms.items()}, open(f'{OUT}/wallhack_confusion.json', 'w'))
    meta.to_csv(f'{OUT}/wallhack_windows_meta.csv', index=False)
    print('done', len(df))


if __name__ == '__main__':
    main()
