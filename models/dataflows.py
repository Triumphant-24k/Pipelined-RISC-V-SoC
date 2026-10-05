"""Executable architectural models: both are models, not two RTL implementations."""
import random,json
from pathlib import Path
def output_stationary(a,b,tile):
 m,k,n=len(a),len(b),len(b[0]);c=[[0]*n for _ in range(m)];reads=0
 for i0 in range(0,m,tile):
  for j0 in range(0,n,tile):
   for z0 in range(0,k,tile):
    av=[row[z0:z0+tile]for row in a[i0:i0+tile]]
    bv=[row[j0:j0+tile]for row in b[z0:z0+tile]]
    reads+=sum(map(len,av))+sum(map(len,bv))
    for i,row in enumerate(av):
     for z,v in enumerate(row):
      for j,w in enumerate(bv[z]):c[i0+i][j0+j]+=v*w
 return c,reads
def weight_stationary(a,b,tile):
 m,k,n=len(a),len(b),len(b[0]);c=[[0]*n for _ in range(m)];reads=0;partial_traffic=0
 for j0 in range(0,n,tile):
  for z0 in range(0,k,tile):
   weights=[row[j0:j0+tile]for row in b[z0:z0+tile]];reads+=sum(map(len,weights))
   for i0 in range(0,m,tile):
    av=[row[z0:z0+tile]for row in a[i0:i0+tile]];reads+=sum(map(len,av))
    partial_traffic+=len(av)*len(weights[0])*4*(1 if z0==0 else 2)
    for i,row in enumerate(av):
     for z,v in enumerate(row):
      for j,w in enumerate(weights[z]):c[i0+i][j0+j]+=v*w
 return c,reads,partial_traffic
def quant(v,bias,relu):return max(-128,min(127,max(0,(v+bias)>>5)if relu else (v+bias)>>5))
def inference():
 image=[1,-2,3,4,5,6,-7,8,9,-10,11,12,13,14,15,-16]
 a=[[image[(r+x)*4+c+y]for x in range(3)for y in range(3)]for r in range(2)for c in range(2)]
 b=[[(z*3+f*7)%9-4 for f in range(2)]for z in range(9)]
 conv,_=output_stationary(a,b,4)
 features=[quant(v,-16 if f else 48,True)for row in conv for f,v in enumerate(row)]
 weights=[[(p*5+c*3)%11-5 for c in range(3)]for p in range(8)]
 dense,_=output_stationary([features],weights,4)
 return {'conv':conv,'features':features,'dense':dense[0],'output':[quant(v,c*16-16,False)for c,v in enumerate(dense[0])]}
def main():
 rng=random.Random(20261005);rows=[]
 for m,n,k in [(7,9,13),(32,32,64),(64,8,128)]:
  a=[[rng.randrange(-128,128)for _ in range(k)]for _ in range(m)]
  b=[[rng.randrange(-128,128)for _ in range(n)]for _ in range(k)]
  ref=[[sum(a[i][z]*b[z][j]for z in range(k))for j in range(n)]for i in range(m)]
  for tile in(4,8):
   os,os_reads=output_stationary(a,b,tile);ws,ws_reads,ps=weight_stationary(a,b,tile)
   assert os==ws==ref
   rows.append({'shape':[m,n,k],'tile':tile,'output_stationary_operand_bytes':os_reads,'weight_stationary_operand_bytes':ws_reads,'weight_stationary_partial_sum_bytes':ps,'timing':'not modeled'})
 root=Path(__file__).resolve().parents[1]
 (root/'reports/dataflow_models.json').write_text(json.dumps({'kind':'functional and idealized traffic models, not RTL timing','experiments':rows,'inference_reference':inference()},indent=2))
 print('PASS dataflow models and independent inference:',inference()['output'])
if __name__=='__main__':main()
