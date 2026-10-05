"""Independent instruction interpreter for retirement differential checks.

This is a project reference model, not a substitute for external ISA certification.
"""
from pathlib import Path
MASK=0xffffffff
def sx(v,bits):return v-(1<<bits)if v&(1<<(bits-1))else v
def muldiv(a,b,f):
 sa,sb=sx(a,32),sx(b,32)
 if f<4:return ((a*b if f in (0,3)else sa*sb if f==1 else sa*b)>>(0 if f==0 else 32))&MASK
 if b==0:return MASK if f<6 else a
 x,y=(sa,sb)if f in(4,6)else(a,b)
 q=abs(x)//abs(y);q=-q if (x<0)!=(y<0)else q
 return (q if f<6 else x-q*y)&MASK
def check_trace(image,trace):
 mem=bytearray(262144);binary=Path(image).read_bytes();mem[:len(binary)]=binary
 r=[0]*32;pc=0;csr={0x300:0x1800,0x304:0,0x305:0,0x340:0,0x341:0,0x342:0,0x343:0};count=0
 for line in Path(trace).read_text().splitlines():
  if line.startswith('TRAP'):
   cause=int(line.split()[1],16);inst=int.from_bytes(mem[pc:pc+4],'little')
   assert cause==11 and inst==0x73,(pc,cause,inst)
   csr[0x341]=pc;csr[0x342]=cause;csr[0x343]=0;csr[0x300]=(csr[0x300]&~0x88)|((csr[0x300]&8)<<4)
   pc=csr[0x305]&~3;continue
  observed_pc,inst,observed_rd,observed_value=(int(x,16)for x in line.split())
  assert observed_pc==pc,f'PC divergence {pc:08x} != {observed_pc:08x}'
  assert inst==int.from_bytes(mem[pc:pc+4],'little'),f'instruction mismatch {pc:08x}'
  op=inst&127;d=(inst>>7)&31;f=(inst>>12)&7;s1=(inst>>15)&31;s2=(inst>>20)&31;f7=inst>>25
  a,b=r[s1],r[s2];imm=sx(inst>>20,12);value=0;dest=0;npc=(pc+4)&MASK
  if op in(0x37,0x17):dest=d;value=(inst&0xfffff000)+(pc if op==0x17 else 0)
  elif op==0x6f:
   j=((inst>>31)<<20)|(((inst>>12)&255)<<12)|(((inst>>20)&1)<<11)|(((inst>>21)&1023)<<1)
   value=npc;dest=d;npc=(pc+sx(j,21))&MASK
  elif op==0x67:value=npc;dest=d;npc=(a+imm)&0xfffffffe
  elif op==0x63:
   offset=((inst>>31)<<12)|(((inst>>7)&1)<<11)|(((inst>>25)&63)<<5)|(((inst>>8)&15)<<1)
   take={0:a==b,1:a!=b,4:sx(a,32)<sx(b,32),5:sx(a,32)>=sx(b,32),6:a<b,7:a>=b}[f]
   if take:npc=(pc+sx(offset,13))&MASK
  elif op in(0x13,0x33):
   dest=d;v=imm&MASK if op==0x13 else b
   if op==0x33 and f7==1:value=muldiv(a,b,f)
   elif f==0:value=a-v if op==0x33 and f7==32 else a+v
   elif f==1:value=a<<(v&31)
   elif f==2:value=int(sx(a,32)<sx(v,32))
   elif f==3:value=int(a<v)
   elif f==4:value=a^v
   elif f==5:value=(sx(a,32)if f7==32 else a)>>(v&31)
   elif f==6:value=a|v
   else:value=a&v
  elif op==3:
   address=(a+imm)&MASK;width=1<<(f&3);dest=d
   value=int.from_bytes(mem[address:address+width],'little',signed=f<4)
  elif op==0x23:
   offset=sx(((inst>>25)<<5)|((inst>>7)&31),12);address=(a+offset)&MASK;width=1<<f
   if address<262144:mem[address:address+width]=(b&((1<<(8*width))-1)).to_bytes(width,'little')
  elif op==0x73:
   if inst==0x30200073:
    npc=csr[0x341];csr[0x300]=(csr[0x300]&~0x88)|((csr[0x300]&0x80)>>4)|0x80
   else:
    address=inst>>20;value=csr.get(address,0);dest=d;v=s1 if f&4 else a
    if f&3==1:csr[address]=v
    elif f&3==2 and s1:csr[address]=value|v
    elif f&3==3 and s1:csr[address]=value&~v
  elif op!=0x0f:raise AssertionError(f'unsupported instruction {inst:08x}')
  assert observed_rd==dest,(pc,observed_rd,dest)
  if dest:
   assert observed_value==value&MASK,f'register divergence pc={pc:08x} x{dest} {observed_value:08x}!={value&MASK:08x}'
   r[dest]=value&MASK
  r[0]=0;pc=npc;count+=1
 return count
