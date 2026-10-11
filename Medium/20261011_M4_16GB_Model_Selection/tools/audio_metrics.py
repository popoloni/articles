#!/usr/bin/env python3
"""Compute throughput from a real audio duration and a measured wall time.
Use 'real' time from: /usr/bin/time -p <your command>. No invented benchmarks.
"""
import argparse
import json
import subprocess
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('audio'); p.add_argument('--wall-seconds', required=True, type=float)
a = p.parse_args()
if a.wall_seconds <= 0: p.error('Positive wall time required.')
cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', a.audio]
data = json.loads(subprocess.check_output(cmd, text=True))
duration = float(data['format']['duration'])
print(json.dumps({'audio_seconds': duration, 'wall_seconds': a.wall_seconds,
                  'audio_seconds_per_wall_second': duration/a.wall_seconds,
                  'note': 'Above 1 means faster than real time; says nothing about accuracy.'}, indent=2))
