import sys, glob, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from brake_pipeline import *
ds=sorted(glob.glob('../files/*'))
fig,ax=plt.subplots(10,3,figsize=(20,26))
for k,d in enumerate(ds):
    x=ax[k%10,k//10]; r=analyze(d)
    x.set_title(os.path.basename(d),fontsize=8)
    if r is None: continue
    x.plot(r['t'],r['a_x'],'b',lw=.8); x.plot(r['t'],r['a_v'],'g',lw=.6,alpha=.6)
    x.axvspan(r['t_start'],r['t_end'],color='orange',alpha=.2)
    x.set_xlim(r['t'][0],r['t'][-1]); x.set_ylim(-14,8); x.grid(alpha=.3)
    x.text(.01,.05,f"dv={r['dv']:.1f} mean={r['mean']:.1f}",transform=x.transAxes,fontsize=8)
plt.tight_layout(); plt.savefig(sys.argv[1],dpi=55)
