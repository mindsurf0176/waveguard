"""Charts from results CSVs + recompute 3 confusion matrices (same code path as run_wallhack.run)."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
import run_wallhack as R

d = pd.read_csv('results/wallhack_results.csv')
agg = d.groupby(['task', 'scheme', 'config', 'model'])[['acc', 'bal_acc', 'majority_baseline']].mean().reset_index()

# --- Chart 1: inflation by evaluation scheme (A_raw = poster pipeline) ---
fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
for ax, task, schemes, labels in [
    (axes[0], 'presence', ['1_random-window-5fold', '2_group-by-recording-5fold', '3_leave-one-setting-out', '4_cross-pair'],
     ['random window\n5-fold', 'group by\nrecording', 'leave-one-\nsetting-out', 'cross pair\n(LOS<->NLOS,\nBQ<->PIFA)']),
    (axes[1], 'location', ['1_random-window-5fold', '2_group-by-recording(w|ww)', '4_cross-pair(system)'],
     ['random window\n5-fold', 'group by\nrecording (w|ww)', 'cross system\n(BQ<->PIFA)'])]:
    x = np.arange(len(schemes)); w = 0.2
    for i, (cfg, mdl, col) in enumerate([('A_raw', 'RF', '#4c72b0'), ('A_raw', 'LR', '#8fb0e0'),
                                          ('E_rel+calib', 'RF', '#dd8452'), ('E_rel+calib', 'LR', '#f2bb90')]):
        v = [agg[(agg.task == task) & (agg.scheme == s) & (agg.config == cfg) & (agg.model == mdl)].bal_acc.values[0] for s in schemes]
        b = ax.bar(x + (i - 1.5) * w, v, w, label=f'{cfg} / {mdl}', color=col)
        for xi, vi in zip(x + (i - 1.5) * w, v): ax.text(xi, vi + 0.01, f'{vi:.2f}', ha='center', fontsize=7)
    chance = 0.5 if task == 'presence' else 0.2
    ax.axhline(chance, ls='--', c='gray'); ax.text(len(schemes) - 0.5, chance + 0.01, 'chance', color='gray', fontsize=8, ha='right')
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8); ax.set_ylim(0, 1.08); ax.set_ylabel('balanced accuracy')
    ax.set_title(f'Wallhack1.8k - {task} ' + ('(empty vs person)' if task == 'presence' else '(room/position 1-5)'))
axes[0].legend(fontsize=7, loc='lower left')
plt.tight_layout(); plt.savefig('results/fig1_accuracy_by_eval_scheme.png', dpi=150); plt.close()

# --- Chart 2: mitigations under leave-one-setting-out (presence) ---
sub = agg[(agg.task == 'presence') & (agg.scheme == '3_leave-one-setting-out')]
cfgs = list(R.CONFIGS); x = np.arange(len(cfgs))
fig, ax = plt.subplots(figsize=(12, 4.5))
for i, (mdl, col) in enumerate([('RF', '#4c72b0'), ('LR', '#dd8452')]):
    v = [sub[(sub.config == c) & (sub.model == mdl)].bal_acc.values[0] for c in cfgs]
    ax.bar(x + (i - 0.5) * 0.38, v, 0.38, label=mdl, color=col)
    for xi, vi in zip(x + (i - 0.5) * 0.38, v): ax.text(xi, vi + 0.01, f'{vi:.2f}', ha='center', fontsize=7)
ax.axhline(0.5, ls='--', c='gray'); ax.set_xticks(x); ax.set_xticklabels(cfgs, rotation=25, ha='right', fontsize=8)
ax.set_ylim(0, 1.08); ax.set_ylabel('balanced accuracy (mean of 4 held-out settings)')
ax.set_title('Presence, train on 3 settings -> test on unseen 4th: which mitigation helps?'); ax.legend()
plt.tight_layout(); plt.savefig('results/fig2_mitigations_leave_one_setting_out.png', dpi=150); plt.close()

# --- Chart 3: confusion matrices (recomputed) ---
ev = ~R.meta.calib.values; m = R.meta
def idx(x): return np.where(x)[0]
R.rows.clear(); R.cms.clear()
pm = ev & (m.act > 0).values
mm = pm & (m.setting == 'NLOS-BQ').values
R.run('location', 'group(w|ww)', 'room', mm, R.group_splits(mm, m.act.astype(str).values, 2), ['A_raw'], 'NLOS-BQ')
R.run('location', 'cross-system', 'room', pm, [(idx(pm & (m.setting == 'NLOS-BQ').values), idx(pm & (m.setting == 'NLOS-PIFA').values))], ['A_raw'], 'NLOS-BQ->NLOS-PIFA')
R.run('presence', 'leave-one-setting-out', 'presence', ev, [(idx(ev & (m.setting != 'NLOS-BQ').values), idx(ev & (m.setting == 'NLOS-BQ').values))], ['A_raw', 'E_rel+calib'], 'test=NLOS-BQ')
picks = [(('location', 'group(w|ww)', 'NLOS-BQ', 'A_raw', 'LR'), 'Location NLOS-BQ\ngroup split (train w, test ww)  LR'),
         (('location', 'cross-system', 'NLOS-BQ->NLOS-PIFA', 'A_raw', 'LR'), 'Location train BQ -> test PIFA\n(same rooms, other antenna)  LR'),
         (('presence', 'leave-one-setting-out', 'test=NLOS-BQ', 'A_raw', 'RF'), 'Presence unseen NLOS-BQ\nA_raw  RF'),
         (('presence', 'leave-one-setting-out', 'test=NLOS-BQ', 'E_rel+calib', 'RF'), 'Presence unseen NLOS-BQ\nE_rel+calib (empty-room calib)  RF')]
fig, axes = plt.subplots(1, 4, figsize=(18, 4.6))
for ax, (k, title) in zip(axes, picks):
    labs, cm = R.cms[k]; cm = np.array(cm); cmn = cm / cm.sum(1, keepdims=True)
    ax.imshow(cmn, cmap='Blues', vmin=0, vmax=1)
    names = ['empty', 'person'] if k[0] == 'presence' else [f'room{l}' for l in labs]
    ax.set_xticks(range(len(labs))); ax.set_yticks(range(len(labs))); ax.set_xticklabels(names, fontsize=8); ax.set_yticklabels(names, fontsize=8)
    for i in range(len(labs)):
        for j in range(len(labs)): ax.text(j, i, cm[i, j], ha='center', va='center', fontsize=8, color='white' if cmn[i, j] > 0.5 else 'black')
    ax.set_xlabel('predicted'); ax.set_ylabel('true'); ax.set_title(title, fontsize=9)
plt.tight_layout(); plt.savefig('results/fig3_confusion_matrices.png', dpi=150); plt.close()
pd.DataFrame(R.rows).to_csv('results/confusion_cases.csv', index=False)
import json; json.dump({'|'.join(k): v for k, v in R.cms.items()}, open('results/wallhack_confusion.json', 'w'))

# --- Chart 4: TU Wien random vs temporal block ---
t = pd.read_csv('results/tuwien_results.csv')
t = t[t.task.str.contains('/raw') & ~t.scheme.str.startswith('3')]
fig, ax = plt.subplots(figsize=(10, 4.2))
tasks = t.task.unique(); schemes = t.scheme.unique(); x = np.arange(len(tasks)); w = 0.13
cols = ['#4c72b0', '#8fb0e0', '#55a868', '#a6d8b0', '#dd8452', '#f2bb90']; i = 0
for s in schemes:
    for mdl in ['RF', 'LR']:
        v = [t[(t.task == tk) & (t.scheme == s) & (t.model == mdl)].bal_acc.values[0] for tk in tasks]
        ax.bar(x + (i - 2.5) * w, v, w, label=f'{s} / {mdl}', color=cols[i]); i += 1
ax.set_xticks(x); ax.set_xticklabels([tk.replace('/raw', '') for tk in tasks], fontsize=8); ax.set_ylim(0, 1.05)
ax.set_ylabel('balanced accuracy'); ax.set_title('TU Wien DP datasets (spectrogram PNGs): random split vs temporal-block split'); ax.legend(fontsize=7, loc='lower left')
plt.tight_layout(); plt.savefig('results/fig4_tuwien_split_comparison.png', dpi=150); plt.close()
print('charts done')
