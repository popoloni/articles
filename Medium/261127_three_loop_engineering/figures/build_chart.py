"""Figure 4: attempts per held-out task, read from the archived demo output."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
r = json.loads((root.parent / 'results/demo_stdout.json').read_text(encoding='utf-8'))
target = {'money_start': 'money', 'text_start': 'text'}[next(k for k in r['policy_change'] if k != 'version')]
names = {'holdout_invoice': 'Invoice', 'holdout_labels': 'Labels', 'holdout_refunds': 'Refunds'}
labels = [names.get(p['task'], p['task']) + ('' if p['family'] == target else '\n(control)') for p in r['pairs']]
base = [p['baseline_attempts'] for p in r['pairs']]
cand = [p['candidate_attempts'] for p in r['pairs']]
accepted = sum(p['baseline_status'] == p['candidate_status'] == 'accepted' for p in r['pairs'])

INK, MUTED, GRID = '#1f2a36', '#5b6773', '#e6e9ed'
BASE, CAND = '#257de0', '#f47230'  # validated categorical pair (CVD-safe)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'text.color': INK, 'axes.labelcolor': MUTED,
                     'xtick.color': INK, 'ytick.color': MUTED})
fig, ax = plt.subplots(figsize=(8.2, 4.8), layout='constrained')
width, gap = 0.34, 0.02  # 2px-ish surface gap between adjacent bars
for i, (b, c) in enumerate(zip(base, cand)):
    for x, h, color in ((i - width / 2 - gap / 2, b, BASE), (i + width / 2 + gap / 2, c, CAND)):
        ax.bar(x, h, width=width, color=color, linewidth=0)
        ax.text(x, h + 0.08, str(h), ha='center', va='bottom', fontsize=12, color=INK)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=BASE, label='Baseline v1'), Patch(color=CAND, label='Candidate v2')],
          frameon=False, loc='upper right', labelcolor=INK)
ax.set_xlim(-0.6, len(labels) - 0.4)
ax.set_xticks(range(len(labels)), labels)
ax.set_ylim(0, 4.2); ax.set_yticks([0, 1, 2, 3, 4]); ax.set_ylabel('Agent attempts')
fig.suptitle(f'Same acceptance result, fewer attempts: {sum(base)} → {sum(cand)}',
             fontweight='bold', fontsize=14, x=0.015, ha='left', color=INK)
ax.set_title(f'Controlled replay · {accepted}/{len(r["pairs"])} held-out tasks accepted under both policies',
             loc='left', fontsize=10.5, color=MUTED, pad=12)
ax.spines[['top', 'right']].set_visible(False)
ax.spines[['left', 'bottom']].set_color('#b8c0c8')
ax.tick_params(axis='x', length=0)
ax.grid(axis='y', color=GRID, linewidth=0.8); ax.set_axisbelow(True)
fig.savefig(root / '04_replay.png', dpi=180)
fig.savefig(root / '04_replay.svg')
plt.close(fig)
