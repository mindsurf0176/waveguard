"""Training-free presence detector: motion score vs. empty-room calibration threshold (per setting).
score = mean over subcarriers of std(amplitude/window-mean) in a 4 s window (feature 'rel' aggregated mean-std).
threshold = max / p99 of the calibration windows (first 20% of the empty recording, excluded from eval)."""
import numpy as np, pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from load_wallhack import recordings, load_file
from features import valid_subcarriers, windows

recs = recordings(); amps = {r['rec']: load_file(r['path'])[0] for r in recs}
V = valid_subcarriers(np.concatenate(list(amps.values())))
rows = []
for s in ['LOS-BQ', 'LOS-PIFA', 'NLOS-BQ', 'NLOS-PIFA']:
    sc, cal, y = [], [], []
    for r in recs:
        if f"{r['scen']}-{r['sys']}" != s: continue
        W = windows(amps[r['rec']][:, V]); R = W / (W.mean(1, keepdims=True) + 1e-6)
        score = R.std(1).mean(1)
        if r['act'] == 0:
            n = int(round(len(W) * 0.2)); cal += list(score[:n]); sc += list(score[n:]); y += [0] * (len(W) - n)
        else:
            sc += list(score); y += [1] * len(W)
    sc, y, cal = np.array(sc), np.array(y), np.array(cal)
    for tname, thr in [('p99', np.percentile(cal, 99)), ('max', cal.max()), ('mean+5sd', cal.mean() + 5 * cal.std())]:
        p = (sc > thr).astype(int)
        rows.append(dict(setting=s, threshold=tname, thr=thr, acc=accuracy_score(y, p), bal_acc=balanced_accuracy_score(y, p),
                         false_alarm_rate=p[y == 0].mean(), miss_rate=1 - p[y == 1].mean(), n_empty=(y == 0).sum(), n_person=(y == 1).sum(),
                         empty_score_median=np.median(sc[y == 0]), person_score_median=np.median(sc[y == 1])))
df = pd.DataFrame(rows); df.to_csv('results/threshold_results.csv', index=False)
print(df.round(3).to_string())
