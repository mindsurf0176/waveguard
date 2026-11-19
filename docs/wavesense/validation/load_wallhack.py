"""Load Wallhack1.8k raw CSI CSVs -> amplitude arrays (packets x 128 subcarrier slots), cached as npz."""
import os, json, glob, numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(__file__), 'data/wallhack1.8k/wallhack1.8k')
CACHE = os.path.join(os.path.dirname(__file__), 'cache'); os.makedirs(CACHE, exist_ok=True)

def load_file(path):
    key = path.replace(ROOT + '/', '').replace('/', '_').replace('.csv', '')
    c = os.path.join(CACHE, key + '.npz')
    if os.path.exists(c):
        d = np.load(c); return d['amp'], d['ts'], d['rssi']
    df = pd.read_csv(path)
    rows = [json.loads(s) for s in df['data']]
    keep = np.array([len(r) == 256 for r in rows])
    if (~keep).sum():
        print(f'  [{key}] dropped {(~keep).sum()} malformed packets (len!=256) of {len(rows)}')
    H = np.array([r for r, k in zip(rows, keep) if k], dtype=np.float32)  # [I,R,I,R...]
    df = df[keep]
    amp = np.sqrt(H[:, 0::2] ** 2 + H[:, 1::2] ** 2)  # sqrt(I^2+Q^2) -> 128 slots
    ts = df['local_timestamp'].values.astype(np.int64); rssi = df['rssi'].values
    np.savez(c, amp=amp, ts=ts, rssi=rssi)
    return amp, ts, rssi

def recordings():
    out = []
    for scen in ['LOS', 'NLOS']:
        for sysm in ['BQ', 'PIFA']:
            for f in sorted(glob.glob(f'{ROOT}/{scen}/{sysm}/*.csv')):
                name = os.path.basename(f)[:-4]
                act = 0 if name.startswith('b') else (2 if name.startswith('ww') else 1)
                room = 0 if act == 0 else int(name[-1])
                out.append(dict(path=f, scen=scen, sys=sysm, name=name, act=act, room=room,
                                rec=f'{scen}/{sysm}/{name}'))
    return out

if __name__ == '__main__':
    for r in recordings():
        a, ts, rs = load_file(r['path'])
        dt = np.diff(ts) / 1000.0  # us -> ms
        print(r['rec'], a.shape, 'median dt(ms)=%.1f' % np.median(dt), 'dur(s)=%.0f' % ((ts[-1]-ts[0])/1e6), 'rssi=%.0f' % rs.mean())
