import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = pd.read_csv('results/drift_results.csv'); M = pd.read_csv('results/drift_stream_meta.csv')
P = np.load('results/drift_preds.npy', allow_pickle=True).item()
meth = ['abs / no-calib', 'abs / fixed-calib', 'abs / EMA (fix1)', 'abs / EMA-safe', 'chg (fix2) / no-calib',
        'chg / fixed-calib', 'chg + EMA (fix1+2)', 'chg + EMA-safe']
sch = ['group-by-recording (within setting)', 'leave-one-setting-out', 'cross-pair']
A = R[R.model != '-'].groupby(['method', 'scheme'])[['bal_acc', 'false_alarm']].mean()  # mean over RF & LR and folds/tags
fig, ax = plt.subplots(1, 3, figsize=(20, 5.2))
x = np.arange(len(meth)); w = 0.27; cols = ['#4c72b0', '#dd8452', '#55a868']
for k, met in enumerate(['bal_acc', 'false_alarm']):
    for i, s in enumerate(sch):
        v = [A.loc[(m, s), met] for m in meth]
        ax[k].bar(x + (i - 1) * w, v, w, label=s, color=cols[i])
        for xi, vi in zip(x + (i - 1) * w, v): ax[k].text(xi, vi + 0.01, f'{vi:.2f}', ha='center', fontsize=6)
    ax[k].set_xticks(x); ax[k].set_xticklabels(meth, rotation=30, ha='right', fontsize=8)
    ax[k].set_title(('Presence balanced accuracy' if met == 'bal_acc' else 'False-alarm rate on empty windows') + ' (mean of RF & LR)', fontsize=10)
    ax[k].set_ylim(0, 1.08)
ax[0].axhline(0.5, ls='--', c='gray'); ax[0].legend(fontsize=7, loc='lower left')
# drift over time inside the empty recording, leave-one-setting-out, LR
e = (M.presence == 0) & (~M.calib)
bins = np.linspace(0.2, 1.0, 9); mid = (bins[:-1] + bins[1:]) / 2 * 10  # minutes into the 10-min recording
for m, c, ls in [('abs / no-calib', 'gray', '-'), ('abs / fixed-calib', '#4c72b0', '-'), ('abs / EMA (fix1)', '#4c72b0', '--'),
                 ('chg / fixed-calib', '#dd8452', '-'), ('chg + EMA (fix1+2)', '#dd8452', '--'), ('chg + EMA-safe', '#55a868', '--')]:
    p = P[f'{m}|leave-one-setting-out|LR']
    fa = [p[e & (M.bpos >= a) & (M.bpos < b)].mean() for a, b in zip(bins[:-1], bins[1:])]
    ax[2].plot(mid, fa, ls, color=c, marker='o', ms=3, label=m)
p = P['threshold / fixed-calib|all|-']
ax[2].plot(mid, [p[e & (M.bpos >= a) & (M.bpos < b)].mean() for a, b in zip(bins[:-1], bins[1:])], ':', c='k', label='threshold / fixed-calib')
ax[2].set_xlabel('minutes into the 10-min empty recording (first 2 min = calibration)'); ax[2].set_ylabel('false-alarm rate')
ax[2].set_title('Drift check: false alarms over time (leave-one-setting-out, LR, 4 settings pooled)', fontsize=10)
ax[2].set_ylim(0, 1.0); ax[2].legend(fontsize=7)
plt.tight_layout(); plt.savefig('results/fig5_drift_fixes.png', dpi=150)
# print the decile numbers too
for m in ['abs / no-calib', 'abs / fixed-calib', 'abs / EMA (fix1)', 'chg / fixed-calib', 'chg + EMA (fix1+2)', 'chg + EMA-safe']:
    p = P[f'{m}|leave-one-setting-out|LR']
    print(m, [round(p[e & (M.bpos >= a) & (M.bpos < b)].mean(), 3) for a, b in zip(bins[:-1], bins[1:])])
