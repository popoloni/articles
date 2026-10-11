#!/usr/bin/env python3
"""Audit the supplied M4 laboratory logs, without importing inference software.

Usage: python analysis/analyze_logs.py /path/to/logs.zip --out analysis
No network calls. Reads ZIP members in memory; never executes archive content.
CSV rows carry original member names and 1-based source lines.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import json
import math
import re
import statistics
import sys
from pathlib import Path, PurePosixPath
from typing import Any
import zipfile

LABELS = {
    'bonsai-binary': 'Bonsai binary · llama.cpp',
    'bonsai-ternary': 'Bonsai packed ternary · MLX-LM',
    'qwen36-stream': 'Qwen3.6 streamed · TurboQuant',
    'qwen38-iq2s': 'Qwen3.8 IQ2_S · llama.cpp',
    'qwen38-q2xl': 'Qwen3.8 Q2_K_XL · llama.cpp',
    'qwen38-iq3xxs': 'Qwen3.8 IQ3_XXS · llama.cpp',
    'qwen38-mlx2': 'Qwen3.8 MLX 2-bit · MLX-LM',
    'qwen38-mlx3': 'Qwen3.8 MLX 3-bit · MLX-LM',
    'qwen38-omlx2': 'Qwen3.8 MLX 2-bit · oMLX',
    'qwen38-omlx3': 'Qwen3.8 MLX 3-bit · oMLX',
}
ORDER = list(LABELS)
EXPECTED_JSON = {'order_id': 'ORD-27A9', 'owner': 'Mira', 'amount_eur': 2400}
EXPECTED_RECALL = 'harbor-mint-47'


def clean_private(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r'/Users/[^/\s"\']+', '$HOME', value)
    if isinstance(value, dict): return {k: clean_private(v) for k,v in value.items()}
    if isinstance(value, list): return [clean_private(v) for v in value]
    return value


def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n',encoding='utf-8')


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text('', encoding='utf-8'); return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)


def read_zip(path: Path) -> dict[str, bytes]:
    members = {}
    with zipfile.ZipFile(path) as z:
        if len(z.infolist()) > 10000 or sum(x.file_size for x in z.infolist()) > 128*1024*1024:
            raise ValueError('Archive exceeds analysis limits.')
        for entry in z.infolist():
            if entry.is_dir(): continue
            p=PurePosixPath(entry.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in entry.filename:
                raise ValueError('Unsafe ZIP path: '+entry.filename)
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Archive symlinks are not supported.')
            if entry.filename in members: raise ValueError('Duplicate ZIP member.')
            members[entry.filename]=z.read(entry)
    return members


def classify(row: dict) -> tuple[str, str, str]:
    choices=(row.get('response') or {}).get('choices',[])
    if len(choices)!=1: return 'invalid_response','', ''
    ch=choices[0]; m=ch.get('message') or {}; text=m.get('content') or ''
    if ch.get('finish_reason')=='length': return 'truncated',text,''
    if ch.get('finish_reason') not in ('stop','tool_calls'): return 'invalid_response',text,''
    if not isinstance(text,str) or not text.strip() or m.get('tool_calls'):
        return 'invalid_response',str(text),''
    if row['case']=='literal_recall':
        return ('pass' if text.strip()==EXPECTED_RECALL else 'wrong_content'),text,''
    if row['case']!='json_contract': return 'unsupported_case',text,''
    try:
        obj=json.loads(text,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (ValueError,TypeError):
        fenced=re.fullmatch(r'\s*```(?:json)?\s*(.*?)\s*```\s*',text,re.S)
        if fenced:
            try:
                obj=json.loads(fenced.group(1))
                if obj==EXPECTED_JSON and type(obj.get('amount_eur')) in (float,int):
                    return 'format_only',text,'Correct fields inside a forbidden Markdown fence; strict test still fails.'
            except (ValueError,TypeError,AttributeError): pass
        return 'invalid_json',text,''
    ok=isinstance(obj,dict) and obj==EXPECTED_JSON and type(obj.get('amount_eur')) in (float,int)
    return ('pass' if ok else 'wrong_content'),text,''


def profile_id(row: dict) -> str:
    rid=row.get('model') or row['request']['model']
    leaf=rid.rsplit('/',1)[-1]
    if ':8000/' in row['base_url'] and leaf in ('qwen38-mlx2','qwen38-mlx3'):
        return leaf.replace('mlx','omlx')
    if leaf not in LABELS: raise ValueError('Unmapped profile: '+rid)
    return leaf


def md_table(rows: list[dict], cols: list[tuple[str,str]]) -> str:
    def fmt(x):
        if x is None: return '—'
        if isinstance(x,float): return f'{x:.3f}'
        return str(x).replace('|','\\|')
    return '\n'.join(['|'+'|'.join(v for k,v in cols)+'|', '|'+'|'.join('---' for _ in cols)+'|']+
                     ['|'+'|'.join(fmt(r.get(k)) for k,v in cols)+'|' for r in rows])


def med(values): return statistics.median(values) if values else None


def audit(path: Path, out: Path) -> dict:
    out.mkdir(parents=True,exist_ok=True)
    members=read_zip(path)
    source_index=[]; normalized=[]; records=[]; readiness=[]; disagreements=[]; seen_ids=set(); duplicates=[]
    case_prompts=collections.defaultdict(set)
    for name,raw in sorted(members.items()):
        text=raw.decode('utf-8',errors='replace')
        source_index.append({'source_file':name,'bytes':len(raw),'sha256':sha(raw),'lines':len(text.splitlines())})
        if not name.endswith('.jsonl'): continue
        session=0; prev_model=None
        for line_no,line in enumerate(text.splitlines(),1):
            if not line.strip(): continue
            r=json.loads(line)
            ch=(r.get('response') or {}).get('choices',[{}])[0]; msg=ch.get('message') or {}
            record_id=(r.get('response') or {}).get('id')
            if record_id in seen_ids: duplicates.append({'source_file':name,'line':line_no,'response_id':record_id})
            seen_ids.add(record_id)
            if 'case' not in r:
                readiness.append({'source_file':name,'source_line':line_no,'utc':r.get('utc'),
                                  'model':clean_private(r['request']['model']),'wall_seconds':r.get('wall_seconds'),
                                  'finish_reason':ch.get('finish_reason'),'text':msg.get('content')})
                continue
            pid=profile_id(r)
            if (r['repeat']==1 and r['case']=='json_contract') or pid!=prev_model: session+=1
            prev_model=pid
            outcome,visible,note=classify(r)
            independently_passed=outcome=='pass'
            if independently_passed!=r['passed']:
                disagreements.append({'source_file':name,'line':line_no,'reported':r['passed'],'recomputed':independently_passed})
            req=r['request']; u=(r.get('response') or {}).get('usage') or r.get('usage') or {}
            timings=r['response'].get('timings') or {}
            case_prompts[r['case']].add(json.dumps(req.get('messages'),sort_keys=True))
            prompt_s=timings.get('prompt_ms'); decode_s=timings.get('predicted_ms')
            if prompt_s is not None: prompt_s/=1000
            else: prompt_s=u.get('prompt_eval_duration')
            if decode_s is not None: decode_s/=1000
            else: decode_s=u.get('generation_duration')
            cached=(u.get('prompt_tokens_details') or {}).get('cached_tokens')
            nt=u.get('prompt_tokens'); ct=u.get('completion_tokens')
            row={
                'source_file':name,'source_line':line_no,'response_id':record_id,'utc':r['utc'],
                'profile':pid,'label':LABELS[pid], 'session':f'{Path(name).name}:suite-{session}',
                'model_id':clean_private(r['model']),'response_model_id':clean_private(r['response'].get('model','')),
                'base_url':r['base_url'],'repeat':r['repeat'],'case':r['case'],
                'passed':independently_passed,'reported_passed':r['passed'],'outcome':outcome,
                'finish_reason':ch.get('finish_reason'),'wall_seconds':r['wall_seconds'],
                'prompt_tokens':nt,'completion_tokens':ct,'cached_tokens':cached,
                'cache_fraction':(cached/nt if cached is not None and nt else None),
                'server_prompt_seconds':prompt_s,'server_decode_seconds':decode_s,
                'server_decode_tps':timings.get('predicted_per_second',u.get('generation_tokens_per_second')),
                'server_prompt_tps':timings.get('prompt_per_second',u.get('prompt_tokens_per_second')),
                'server_ttft_seconds':u.get('time_to_first_token'),
                'server_total_seconds':u.get('total_time'), 'model_load_seconds':u.get('model_load_duration'),
                'timing_source':'llama.cpp response.timings' if timings else ('oMLX response.usage' if 'generation_duration' in u else 'none'),
                'visible_characters':len(visible),'reasoning_characters':len(msg.get('reasoning_content') or msg.get('thinking') or ''),
                'temperature':req.get('temperature'), 'max_tokens':req.get('max_tokens'),'stream':req.get('stream'),
                'tool_executed':r.get('tool_executed'), 'fingerprint':r['response'].get('system_fingerprint'),
                'error':r.get('error',''),'audit_note':note,
                'request_hash_without_model':sha(json.dumps({k:v for k,v in req.items() if k!='model'},sort_keys=True).encode()),
            }
            if not isinstance(row['wall_seconds'],(float,int)) or not math.isfinite(row['wall_seconds']) or row['wall_seconds']<0:
                raise ValueError('Invalid wall-time value.')
            normalized.append(row)
            records.append({'source_file':name,'source_line':line_no,'profile':pid,'session':row['session'],
                            'recomputed_outcome':outcome,'record':clean_private(r)})
    write_csv(out/'source-index.csv',source_index)
    write_csv(out/'request-metrics.csv',normalized)
    write_json(out/'request-metrics.json',normalized)
    write_json(out/'readiness.json',readiness)
    with (out/'response-records.jsonl').open('w',encoding='utf-8') as f:
        for r in records: f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n')
    summary=[]; by_case=[]; by_session=[]
    for pid in ORDER:
        rows=[r for r in normalized if r['profile']==pid]
        if not rows: continue
        good=[r for r in rows if r['passed']]; bad=[r for r in rows if not r['passed']]
        s={'profile':pid,'label':LABELS[pid],'n':len(rows),'passes':len(good),'failures':len(bad),
           'truncated':sum(r['outcome']=='truncated' for r in rows),
           'format_only':sum(r['outcome']=='format_only' for r in rows),
           'suites':len(set(r['session'] for r in rows)),
           'median_wall_seconds':med([r['wall_seconds'] for r in rows]),
           'total_wall_seconds':sum(r['wall_seconds'] for r in rows),
           'failed_wall_seconds':sum(r['wall_seconds'] for r in bad),
           'completion_tokens':sum(r['completion_tokens'] for r in rows),
           'failed_completion_tokens':sum(r['completion_tokens'] for r in bad),
           'with_reasoning':sum(r['reasoning_characters']>0 for r in rows),
           'fingerprints':'; '.join(sorted({r['fingerprint'] for r in rows if r['fingerprint']}))}
        for case in ['json_contract','literal_recall']:
            rr=[r for r in rows if r['case']==case]; wall=[r['wall_seconds'] for r in rr]
            s[case+'_passes']=sum(r['passed'] for r in rr);s[case+'_n']=len(rr)
            s[case+'_median_s']=med(wall)
            by_case.append({'profile':pid,'label':LABELS[pid],'case':case,'n':len(rr),
                            'passes':sum(r['passed'] for r in rr),'median_s':med(wall),'min_s':min(wall),'max_s':max(wall),
                            'median_tokens':med([r['completion_tokens'] for r in rr]),
                            'median_server_decode_tps':med([r['server_decode_tps'] for r in rr if r['server_decode_tps'] is not None])})
        summary.append(s)
        for sess in dict.fromkeys(r['session'] for r in rows):
            rr=[r for r in rows if r['session']==sess]
            by_session.append({'profile':pid,'session':sess,'n':len(rr),'passes':sum(r['passed'] for r in rr),
                               'utc_start':rr[0]['utc'],'utc_last_request_start':rr[-1]['utc'],
                               'json_median_s':med([r['wall_seconds'] for r in rr if r['case']=='json_contract']),
                               'recall_median_s':med([r['wall_seconds'] for r in rr if r['case']=='literal_recall'])})
    write_csv(out/'profile-summary.csv',summary);write_json(out/'profile-summary.json',summary)
    write_csv(out/'case-summary.csv',by_case);write_csv(out/'suite-summary.csv',by_session)

    # Standalone CLI observations. Retain the printed unit; do not reconcile two differently printed peaks silently.
    cli=[]
    for filename,profile,review in [
        ('ternary-generate.log','bonsai-ternary','Coherent five-sentence answer; no separate exit-status file.'),
        ('qwen38-mlx2-generate.log','qwen38-mlx2','Meta-commentary and malformed trailing text; not a satisfactory final answer.'),
        ('qwen38-tq-diagnostic.log','qwen38-tq-diagnostic','Coherent five-sentence answer; paired exit-code file is 0. Not a coding/agent test.')]:
        name='logs/'+filename;text=members[name].decode('utf-8',errors='replace'); pp={}
        for lineno,line in enumerate(text.splitlines(),1):
            m=re.search(r'Prompt: (\d+) tokens, ([\d.]+) tokens-per-sec',line)
            if m: pp.update(prompt_tokens=int(m[1]),prompt_tps=float(m[2]),prompt_source_line=lineno)
            m=re.search(r'Generation: (\d+) tokens, ([\d.]+) tokens-per-sec',line)
            if m: pp.update(generation_tokens=int(m[1]),generation_tps=float(m[2]),generation_source_line=lineno)
            m=re.search(r'^Peak memory: ([\d.]+) GB$',line)
            if m: pp.update(peak_memory_printed_gb=float(m[1]),memory_source_line=lineno)
            m=re.search(r'^peak memory: ([\d.]+) GB$',line)
            if m: pp.update(second_peak_memory_printed_gb=float(m[1]),second_memory_source_line=lineno)
        cli.append({'profile':profile,'source_file':name,**pp,'qualitative_review':review})
    write_csv(out/'cli-observations.csv',cli);write_json(out/'cli-observations.json',cli)

    provenance=[]
    for name,b in members.items():
        if name.endswith('-launch.json'):
            r=json.loads(b); provenance.append({'source_file':name,'profile':Path(name).name.removesuffix('-launch.json'),
                        'repository':r.get('repo'),'revision':r.get('revision'),'os':r.get('os'),
                        'command':clean_private(json.dumps(r.get('command'),ensure_ascii=False))})
    write_csv(out/'checkpoint-provenance.csv',provenance)
    audit_result={'source_archive':path.name,'archive_sha256':sha(path.read_bytes()),
        'source_files':len(members),'expanded_bytes':sum(len(x) for x in members.values()),
        'smoke_records':len(normalized),'readiness_records':len(readiness),
        'profiles_with_smoke':len(summary),'smoke_suites':len(by_session),
        'passed':sum(r['passed'] for r in normalized),'failed':sum(not r['passed'] for r in normalized),
        'truncated':sum(r['outcome']=='truncated' for r in normalized),
        'reported_recomputed_disagreements':disagreements,'duplicate_response_ids':duplicates,
        'unique_input_messages_per_case':{k:len(v) for k,v in case_prompts.items()},
        'all_smoke_temperatures':sorted({r['temperature'] for r in normalized}),
        'all_smoke_output_budgets':sorted({r['max_tokens'] for r in normalized}),
        'all_smoke_streaming_values':sorted({r['stream'] for r in normalized}),
        'api_token_count_consistency':all(r['completion_tokens']+r['prompt_tokens']==
               records[i]['record']['response']['usage']['total_tokens'] for i,r in enumerate(normalized)),
        'tools_executed':sum(bool(r['tool_executed']) for r in normalized),
        'total_wall_seconds':sum(r['wall_seconds'] for r in normalized),
        'failed_wall_seconds':sum(r['wall_seconds'] for r in normalized if not r['passed']),
        'total_completion_tokens':sum(r['completion_tokens'] for r in normalized),
        'failed_completion_tokens':sum(r['completion_tokens'] for r in normalized if not r['passed']),
        'unique_dates_utc':sorted({r['utc'][:10] for r in normalized}),
        'scope':'Historical supplied short text tests only; no new model inference performed.'}
    if disagreements or duplicates: raise ValueError('Audit disagreement or duplicate detected; review before publication.')
    write_json(out/'audit.json',audit_result)
    return {'audit':audit_result,'summary':summary,'case_summary':by_case,'cli':cli,'rows':normalized,'members':members}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('archive',type=Path);ap.add_argument('--out',type=Path,default=Path('analysis'))
    args=ap.parse_args(); result=audit(args.archive,args.out); print(json.dumps(result['audit'],indent=2))
    print(md_table(result['summary'],[('label','Model/runtime'),('passes','Pass'),('n','N'),('json_contract_median_s','JSON median s'),('literal_recall_median_s','Recall median s')]))
if __name__=='__main__': main()
