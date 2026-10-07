#!/usr/bin/env python3
"""Create eight independent matplotlib figures from audited request metrics.
No fabricated values, subplots, custom palette or decorative styles.
"""
from pathlib import Path
import argparse
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ORDER=['bonsai-binary','bonsai-ternary','qwen36-stream','qwen38-iq2s','qwen38-q2xl','qwen38-iq3xxs','qwen38-mlx2','qwen38-mlx3','qwen38-omlx2','qwen38-omlx3']
SHORT={
 'bonsai-binary':'Bonsai binary | llama.cpp', 'bonsai-ternary':'Bonsai ternary | MLX-LM',
 'qwen36-stream':'Qwen3.6 streamed | TurboQuant', 'qwen38-iq2s':'Qwen3.8 IQ2_S | llama.cpp',
 'qwen38-q2xl':'Qwen3.8 Q2_K_XL | llama.cpp', 'qwen38-iq3xxs':'Qwen3.8 IQ3_XXS | llama.cpp',
 'qwen38-mlx2':'Qwen3.8 2-bit | MLX-LM', 'qwen38-mlx3':'Qwen3.8 3-bit | MLX-LM',
 'qwen38-omlx2':'Qwen3.8 2-bit | oMLX', 'qwen38-omlx3':'Qwen3.8 3-bit | oMLX'}


def base(title,subtitle,height=7.8):
 fig,ax=plt.subplots(figsize=(12.8,height))
 fig.suptitle(title,x=.04,y=.97,ha='left',fontsize=19,fontweight='bold')
 fig.text(.04,.91,subtitle,ha='left',va='top',fontsize=10.5)
 ax.tick_params(labelsize=10.5)
 return fig,ax


def save(fig,ax,out,name,foot,left=.31):
 fig.subplots_adjust(left=left,right=.94,top=.82,bottom=.17)
 fig.text(.04,.045,foot,ha='left',va='bottom',fontsize=9.5,linespacing=1.4)
 ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
 fig.savefig(out/(name+'.png'),dpi=180)
 fig.savefig(out/(name+'.svg'))
 plt.close(fig)


def make_all(data_dir:Path,output_dir:Path)->list[str]:
 output_dir.mkdir(parents=True,exist_ok=True)
 d=pd.read_csv(data_dir/'request-metrics.csv')
 s=pd.read_csv(data_dir/'profile-summary.csv').set_index('profile')
 names=[]
 # 1. Outcomes are counts, not confidence estimates.
 fig,ax=base('A model can answer and still fail the contract',
             '66 recorded smoke requests; two fixed tasks. Repeated prompts are not independent benchmark questions.')
 y=np.arange(len(ORDER));left=np.zeros(len(ORDER))
 cats=[('pass','Passed'),('other','Completed, contract failed'),('truncated','Output budget exhausted')]
 for cat,label in cats:
  vals=[]
  for p in ORDER:
   r=d[d.profile==p]
   vals.append(int((r.outcome==cat).sum()) if cat!='other' else int((~r.outcome.isin(['pass','truncated'])).sum()))
  ax.barh(y,vals,left=left,label=label,height=.65);left+=vals
 for i,p in enumerate(ORDER): ax.text(left[i]+.12,i,f"{int(s.loc[p,'passes'])}/{int(s.loc[p,'n'])} passed",va='center',fontsize=9.5)
 ax.set_yticks(y,[SHORT[p] for p in ORDER]);ax.invert_yaxis();ax.set_xlim(0,15.5);ax.set_xticks([0,3,6,9,12]);ax.set_xlabel('Recorded requests',fontsize=11)
 fig.legend(*ax.get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.04,.86),ncol=3,frameon=False,fontsize=9.5)
 name='01-contract-outcomes';names.append(name)
 save(fig,ax,output_dir,name,'Source: uploaded logs.zip; strict checks independently re-evaluated. No tool execution or coding task is tested.\nBonsai ternary includes two six-request suites. All other model/runtime configurations have one suite.')
 # 2,3. Per-task observations and median; retain failures.
 for case,num,title in [('json_contract','02','Time to return the requested JSON'),('literal_recall','03','Time to return the supplied code')]:
  fig,ax=base(title,'Client end-to-end wall time. Dots are individual requests; bars mark medians. Failed answers remain visible.')
  point_groups = {True: ([], []), False: ([], [])}
  med_x=[]; med_y=[]
  for i,p in enumerate(ORDER):
   r=d[(d.profile==p)&(d.case==case)]
   jit=np.linspace(-.13,.13,len(r));good=r.passed.to_numpy(dtype=bool)
   for passed in (True,False):
    mask=good if passed else ~good
    point_groups[passed][0].extend(r.wall_seconds.to_numpy()[mask])
    point_groups[passed][1].extend(i+jit[mask])
   median=float(r.wall_seconds.median()); med_x.append(median); med_y.append(i)
   ax.text(1.01,i,f'{median:.2f} s   {int(good.sum())}/{len(r)} pass',transform=ax.get_yaxis_transform(),va='center',fontsize=9.5)
  for passed,marker,label in [(True,'o','Passed'),(False,'x','Failed')]:
   ax.scatter(*point_groups[passed],marker=marker,s=40 if passed else 54,label=label)
  ax.scatter(med_x,med_y,marker='|',s=330,linewidths=2,label='Median')
  ax.set_yticks(y,[SHORT[p] for p in ORDER]);ax.invert_yaxis();ax.set_xscale('log');ax.set_xlim(.45,80);ax.set_xticks([.5,1,2,5,10,20,50],['0.5','1','2','5','10','20','50']);ax.set_xlabel('Seconds per request (log scale)',fontsize=11);ax.grid(axis='x',alpha=.2)
  fig.legend(*ax.get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.31,.86),ncol=3,frameon=False,fontsize=9.5)
  name=f'{num}-{case}-latency';names.append(name)
  # Leave additional space for the exact summary labels at right.
  fig.subplots_adjust(left=.31,right=.77,top=.82,bottom=.17)
  fig.text(.04,.045,'Source: request JSONL records, 5–6 October 2026. N=3 per task, except ternary Bonsai N=6.\nTemplates, caching, reasoning, output lengths and prior warm-up differ; this is not an isolated engine benchmark.',fontsize=9.5)
  ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
  fig.savefig(output_dir/(name+'.png'),dpi=180);fig.savefig(output_dir/(name+'.svg'));plt.close(fig)
 # 4. True decode data from comparable telemetry family only.
 ps=['bonsai-binary','qwen38-iq2s','qwen38-q2xl','qwen38-iq3xxs']
 fig,ax=base('GGUF decoding: similar Qwen3.8 rates, different reply lengths',
             'JSON task only. Native response.timings.predicted_per_second; never total tokens divided by request latency.',6.4)
 for i,p in enumerate(ps):
  r=d[(d.profile==p)&(d.case=='json_contract')];vals=r.server_decode_tps
  ax.scatter(vals,i+np.linspace(-.12,.12,len(r)),s=48)
  ax.scatter([vals.median()],[i],marker='|',s=400,linewidths=2)
  ax.text(1.01,i,f'{vals.median():.2f} tok/s\n{int(r.completion_tokens.min())}–{int(r.completion_tokens.max())} output tokens',transform=ax.get_yaxis_transform(),va='center',fontsize=10)
 ax.set_yticks(np.arange(len(ps)),[SHORT[p] for p in ps]);ax.invert_yaxis();ax.set_xlim(0,17);ax.set_xlabel('Runtime-reported decode tokens per second',fontsize=11);ax.grid(axis='x',alpha=.2)
 name='04-gguf-decode';names.append(name)
 fig.subplots_adjust(left=.31,right=.79,top=.80,bottom=.20)
 fig.text(.04,.045,'N=3 per row. Qwen3.8: same b11429 build; Bonsai: Prism b10743. One binary JSON answer failed formatting.\nTiming counters use runtime-specific token conventions; short completions are not sustained-throughput tests.',fontsize=9.5)
 ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
 fig.savefig(output_dir/(name+'.png'),dpi=180);fig.savefig(output_dir/(name+'.svg'));plt.close(fig)
 # 5. Actual logged prompt-evaluation times, not nominal cache size.
 ps=ps+['qwen38-omlx2','qwen38-omlx3']
 fig,ax=base('Prefix reuse reduces prompt work, not all response time',
             'JSON task. First occurrence versus median of repeats 2–3; native prompt-evaluation durations.',7.1)
 first=[];later=[]
 for p in ps:
  r=d[(d.profile==p)&(d.case=='json_contract')]
  first.append(float(r[r['repeat']==1].server_prompt_seconds.iloc[0]))
  later.append(float(r[r['repeat']>1].server_prompt_seconds.median()))
 y6=np.arange(len(ps));ax.barh(y6-.17,first,height=.3,label='First occurrence: 0 prefix tokens reused');ax.barh(y6+.17,later,height=.3,label='Later repeats: logged prefix reuse')
 for i,(a,b) in enumerate(zip(first,later)): ax.text(max(a,b)+.025,i,f'{a:.2f} → {b:.2f} s',va='center',fontsize=10)
 ax.set_yticks(y6,[SHORT[p] for p in ps]);ax.invert_yaxis();ax.set_xlim(0,max(first)*1.36);ax.set_xlabel('Server prompt-evaluation seconds',fontsize=11);fig.legend(*ax.get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.04,.86),ncol=2,frameon=False,fontsize=9.1)
 name='05-prefix-prefill';names.append(name)
 save(fig,ax,output_dir,name,'Later JSON repeats: 68/72 prefix tokens reused in GGUF; 107/112 in oMLX. Models can still produce wrong answers.\nA first occurrence is not proof of a cold machine; these observations do not test persistence across a restart.')
 # 6. Token budget includes reasoning; exact hidden split not available.
 fig,ax=base('oMLX’s passing 3-bit run generated much more than the final answer',
             'Median completion tokens, three requests per task. The oMLX responses all include reasoning_content.',6.4)
 groups=['JSON record','Literal code'];x=np.arange(2);w=.32
 for offset,p,label in [(-w/2,'qwen38-mlx3','Standalone MLX-LM'),(w/2,'qwen38-omlx3','oMLX, reasoning present')]:
  vals=[float(d[(d.profile==p)&(d.case==c)].completion_tokens.median()) for c in ['json_contract','literal_recall']]
  bars=ax.bar(x+offset,vals,width=w,label=label)
  ax.bar_label(bars,fmt='%.0f',padding=5,fontsize=12)
 ax.set_xticks(x,groups);ax.set_ylabel('Reported completion tokens',fontsize=11);ax.set_ylim(0,200);ax.legend(loc='upper right',frameon=False,fontsize=10)
 name='06-reasoning-workload';names.append(name)
 save(fig,ax,output_dir,name,'Standalone input counts: 72 / 47 tokens. oMLX input counts: 112 / 87. Templates are not matched.\nReasoning-token counts are not separately logged; these are whole-completion counts, not counts of reasoning alone.',left=.10)
 # 7 & 8. Separate CLI smoke; retain malfunctioning model.
 cli=pd.read_csv(data_dir/'cli-observations.csv')
 clabels=['Bonsai packed ternary\nCoherent final answer','Qwen3.8 MLX 2-bit\nMalformed / meta-commentary','Qwen3.8 TQ diagnostic\nCoherent final answer; exit 0']
 for field,num,title,xlabel,foot in [
 ('generation_tps','07','Standalone generation: speed is not a quality score','CLI-reported generation tokens per second',
  'One CLI observation per row, not the HTTP smoke suite. Output lengths: 133, 135 and 133 tokens.\nThe 2-bit output is not accepted as a satisfactory answer. No coding or tool task is established by these samples.'),
 ('peak_memory_printed_gb','08','Only three CLI runs report peak memory','Runtime peak value (GB, as printed)',
  'One runtime-local peak per CLI run; not total system memory or a sustained memory-pressure measurement.\nThe TQ diagnostic also prints “peak memory: 11.92 GB”; both labels are retained in the evidence, not averaged.')]:
  fig,ax=base(title,'Same short retry-versus-rollback task family. No missing memory or throughput values have been filled in.',6.6)
  vals=cli[field].to_numpy();bars=ax.barh(np.arange(3),vals,height=.55)
  ax.set_yticks(np.arange(3),clabels);ax.invert_yaxis();ax.set_xlim(0,max(vals)*1.25)
  ax.bar_label(bars,labels=[f'{v:.3f}' for v in vals],padding=7,fontsize=11);ax.set_xlabel(xlabel,fontsize=11);ax.grid(axis='x',alpha=.2)
  name=f'{num}-cli-'+('decode' if num=='07' else 'memory');names.append(name);save(fig,ax,output_dir,name,foot,left=.32)
 (output_dir/'figure-manifest.json').write_text(json.dumps({'figures':names,'renderer':'matplotlib','individual_axes':True,'palette':'matplotlib defaults'},indent=2)+'\n')
 return names

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--data',type=Path,default=Path('analysis'));ap.add_argument('--out',type=Path,default=Path('figures'));a=ap.parse_args()
 print('\n'.join(make_all(a.data,a.out)))
