"""TU Wien ICVS2023 (Zenodo 8021099) DP_LOS / DP_NLOS: only 400x52 amplitude spectrogram PNGs are published (no raw CSI,
no recording ids). Sorted by index, every class is ONE contiguous block -> each class is (very likely) one recording.
So a recording-level split is impossible; best honest proxy = contiguous temporal-block split inside each class block."""
import csv, os, json, numpy as np, pandas as pd
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
from features import feat_raw, feat_rel

D = 'data'; OUT = 'results'; SEED = 0
MODELS = {
    'RF': lambda: RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=SEED, class_weight='balanced'),
    'LR': lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1, class_weight='balanced')),
}
def load(ds):
    p = f'{D}/{ds}/{ds}'; lab = {}; split = {}
    for f, sname in [('trainLabels.csv', 'train'), ('validationLabels.csv', 'train'), ('testLabels.csv', 'test')]:
        for r in csv.reader(open(f'{p}/{f}')):
            if r: lab[int(r[0])] = int(r[1]); split[int(r[0])] = sname
    ids = sorted(lab)
    W = np.stack([np.asarray(Image.open(f'{p}/{i}.png'), dtype=np.float32) / 255.0 for i in ids])  # (n,400,52)
    y = np.array([lab[i] for i in ids]); sp = np.array([split[i] for i in ids])
    # temporal block id inside each class block (5 contiguous chunks)
    blk = np.zeros(len(ids), int)
    for c in np.unique(y):
        ii = np.where(y == c)[0]; blk[ii] = np.minimum(4, (np.arange(len(ii)) * 5) // len(ii))
    return W, y, sp, blk

rows, cms = [], {}
def ev(name, scheme, X, y, splits):
    for mn, mk in MODELS.items():
        accs, baccs, majs, ys, ps = [], [], [], [], []
        for tr, te in splits:
            m = mk().fit(X[tr], y[tr]); p = m.predict(X[te])
            accs.append(accuracy_score(y[te], p)); baccs.append(balanced_accuracy_score(y[te], p))
            _, c = np.unique(y[te], return_counts=True); majs.append(c.max() / c.sum()); ys.append(y[te]); ps.append(p)
        rows.append(dict(task=name, scheme=scheme, model=mn, acc=np.mean(accs), bal_acc=np.mean(baccs),
                         majority_baseline=np.mean(majs), n_test=sum(len(t) for _, t in splits)))
        yc, pc = np.concatenate(ys), np.concatenate(ps)
        cms[f'{name}|{scheme}|{mn}'] = (sorted(map(int, np.unique(y))), confusion_matrix(yc, pc, labels=sorted(np.unique(y))).tolist())
        print(f'{name:28s} {scheme:40s} {mn} acc={np.mean(accs):.3f} bal={np.mean(baccs):.3f} maj={np.mean(majs):.3f}', flush=True)

data = {ds: load(ds) for ds in ['DP_LOS', 'DP_NLOS']}
for ds, (W, y, sp, blk) in data.items():
    for fn, F in [('raw', feat_raw), ('rel', feat_rel)]:
        X = F(W)
        for tname, yy in [('room6(0=empty,1-5)', y), ('presence', (y > 0).astype(int))]:
            nm = f'{ds}/{tname}/{fn}'
            ev(nm, '1_provided-8:1:1-split(random)', X, yy, [(np.where(sp == 'train')[0], np.where(sp == 'test')[0])])
            ev(nm, '2_temporal-block-5fold', X, yy, [(np.where(blk != k)[0], np.where(blk == k)[0]) for k in range(5)])
            # strict: train on first 60% of each block, test last 20% (gap of 20%)
            ev(nm, '2b_train-first60%-test-last20%', X, yy, [(np.where(blk <= 2)[0], np.where(blk == 4)[0])])
# cross-environment presence: LOS <-> NLOS
for fn, F in [('raw', feat_raw), ('rel', feat_rel)]:
    (Wa, ya, _, _), (Wb, yb, _, _) = data['DP_LOS'], data['DP_NLOS']
    Xa, Xb = F(Wa), F(Wb); X = np.concatenate([Xa, Xb]); yy = np.concatenate([ya > 0, yb > 0]).astype(int)
    ia, ib = np.arange(len(Xa)), np.arange(len(Xa), len(X))
    ev(f'presence/{fn}', '3_cross DP_LOS->DP_NLOS', X, yy, [(ia, ib)])
    ev(f'presence/{fn}', '3_cross DP_NLOS->DP_LOS', X, yy, [(ib, ia)])
pd.DataFrame(rows).to_csv(f'{OUT}/tuwien_results.csv', index=False)
json.dump(cms, open(f'{OUT}/tuwien_confusion.json', 'w'))
for ds, (W, y, sp, blk) in data.items():
    print(ds, 'class counts', dict(zip(*np.unique(y, return_counts=True))))
