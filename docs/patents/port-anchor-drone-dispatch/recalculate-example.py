import math,json
from pathlib import Path
nodes={'O':(0,0,0),'V1':(2000,0,20),'V2':(4000,0,20),'V3':(0,3000,20),'V4':(1000,1000,20),'V5':(-3000,0,20)}
weights={'V1':8,'V2':6,'V3':10,'V4':5,'V5':12}
models={'A':dict(m0=70,Q=25,v=12,L0=25000,LF=20000,E=4.5,T=1800),'B':dict(m0=65,Q=30,v=15,L0=28000,LF=16000,E=4.0,T=2400)}
def flight(g,visits):
    m=models[g]; q=sum(weights[v] for v in visits); t=0.; E=0.; completion={}; segs=[]
    route=['O']+visits+['O']
    for a,b in zip(route,route[1:]):
        x,y,z=nodes[a]; xx,yy,zz=nodes[b]; d=math.hypot(xx-x,yy-y)
        dt=(60-z)/3+d/m['v']+(60-zz)/3
        L=m['L0']-(m['L0']-m['LF'])*(q/m['Q'])**1.5
        de=d*m['E']/L+(m['m0']+q)*9.81*(60-z)/(3.6e6*.72)
        t+=dt; E+=de; segs.append(dict(a=a,b=b,q=q,t=dt,E=de))
        if b!='O':
            t+=60; E+=4*60/3600; completion[b]=t; q-=weights[b]
    soc=1-E/m['E']
    chg=m['T']*(.65*(.9-soc)/.9+.35) if soc<.9 else m['T']*.35*(1-soc)/.1
    return dict(duration=t,E=E,soc=soc,chg=chg,completion=completion,segs=segs)
r={p:flight(g,vs) for p,g,vs in [('P1','A',['V1','V2']),('P2','A',['V3']),('P3','A',['V4']),('P4','B',['V5'])]}
c2=r['P2']['duration']+r['P2']['chg']; c1=c2+r['P1']['chg']; s3=c2+60; f3=s3+r['P3']['duration']; c3=max(c1,f3)+r['P3']['chg']
bready=r['P4']['duration']+r['P4']['chg']; bvisit=flight('B',['V4'])
results={'tasks':r,'P2_charge_end':c2,'P1_charge_end':c1,'P3_start':s3,'P3_V4_completion':s3+r['P3']['completion']['V4'],'P3_return':f3,'P3_charge_end':c3,'total_E':sum(x['E'] for x in r.values()),'B_P3_completion':bready+60+bvisit['completion']['V4'],'reverse_P1':flight('A',['V2','V1'])}
assert abs(results['total_E']-4.471623)<.000001
assert abs(results['P3_V4_completion']-1745.734)<.001
assert abs(c3-3128.640)<.001
assert results['B_P3_completion']>1800
assert results['reverse_P1']['completion']['V1']>400
Path(__file__).with_name('example-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in results.items() if k not in ['tasks','reverse_P1']},indent=2))
