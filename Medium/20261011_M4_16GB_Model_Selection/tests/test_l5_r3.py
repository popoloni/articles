"""R3 regressions: no native runtime, model or real memory-setting operation."""
from __future__ import annotations
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import venv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import launch_lab as launch


def source_fixture():
    text = 'raise RuntimeError("MUST NOT IMPORT THIS FIXTURE")\nimport argparse\n'
    functions = {}
    for flag, function in launch.TQ_WRAPPER_PARSERS.items():
        functions.setdefault(function, []).append(flag)
    for name, flags in functions.items():
        text += f'\ndef {name}(argv):\n    parser = argparse.ArgumentParser(add_help=False)\n'
        for flag in flags:
            text += f'    parser.add_argument({flag!r})\n'
        text += '    return parser.parse_known_args(argv)\n'
    text += '\ndef main():\n'
    for name in functions:
        text += f'    value, remaining = {name}([])\n'
    return text


class WrapperDiscovery(unittest.TestCase):
    def test_all_required_wrapper_options_found(self):
        self.assertEqual(launch.wrapper_flags_from_source(source_fixture()), launch.TQ_WRAPPER_PARSERS)

    def test_source_is_not_executed(self):
        self.assertIn('--tool-syntax-greedy', launch.wrapper_flags_from_source(source_fixture()))

    def test_docstring_mention_is_not_a_declaration(self):
        source = source_fixture().replace("parser.add_argument('--tool-syntax-greedy')", "pass # --tool-syntax-greedy")
        self.assertNotIn('--tool-syntax-greedy', launch.wrapper_flags_from_source(source))

    def test_unused_preparser_not_accepted(self):
        source = source_fixture().replace('    value, remaining = _extract_tool_syntax_greedy_args([])\n', '')
        self.assertNotIn('--tool-syntax-greedy', launch.wrapper_flags_from_source(source))

    def test_not_parsed_preparser_not_accepted(self):
        source = source_fixture().replace('return parser.parse_known_args(argv)', 'return None, argv')
        self.assertEqual(launch.wrapper_flags_from_source(source), {})

    def test_invalid_source_fails_closed(self):
        with self.assertRaises(launch.LaunchError):
            launch.wrapper_flags_from_source('def main(:')

    def test_missing_main_fails_closed(self):
        with self.assertRaises(launch.LaunchError):
            launch.wrapper_flags_from_source('import argparse')

    def test_options_hidden_from_help_are_preserved(self):
        cmd = launch.command('qwen36-asym', '/tmp/lab')
        before = list(cmd)
        help_text = ' '.join(launch.flags_in_command(cmd) - launch.TQ_WRAPPER_PARSERS.keys())
        launch.validate_flags(cmd, help_text, launch.wrapper_flags_from_source(source_fixture()))
        self.assertEqual(cmd, before)
        self.assertIn('--tool-syntax-greedy', cmd)

    def test_genuinely_missing_option_still_fails(self):
        cmd = launch.command('qwen36-asym', '/tmp/lab')
        with self.assertRaisesRegex(launch.LaunchError, 'tool-syntax-greedy'):
            launch.validate_flags(cmd, ' '.join(cmd), {'--kv-bits':'_extract_kv_args'})

    def test_unknown_downstream_option_still_fails(self):
        with self.assertRaises(launch.LaunchError):
            launch.validate_flags(['mlx_lm.server','--unknown'], '--unknown-longer')

    def test_normal_downstream_options_pass(self):
        launch.validate_flags(['mlx_lm.server','--model','/tmp/x','--port','8081'], '--model MODEL\n--port PORT')

    def test_other_runtime_cannot_borrow_wrapper_flags(self):
        with self.assertRaises(launch.LaunchError):
            launch.validate_flags(['mlx_lm.server','--kv-bits','8'], '', launch.TQ_WRAPPER_PARSERS)

    def test_streaming_native_routing_and_disk_cache_preserved(self):
        cmd = launch.command('qwen36-stream','/tmp/lab',True)
        helper = ' '.join(launch.flags_in_command(cmd) - launch.TQ_WRAPPER_PARSERS.keys())
        launch.validate_flags(cmd, helper, launch.TQ_WRAPPER_PARSERS)
        self.assertEqual(cmd[cmd.index('--max-active-experts')+1], '0')
        self.assertIn('--disk-cache',cmd)

    def test_failed_help_does_not_start_source_probe(self):
        with mock.patch.object(launch.subprocess,'run',return_value=subprocess.CompletedProcess([],2,'','bad')):
            with mock.patch.object(launch,'inspect_turboquant') as inspect:
                with self.assertRaises(launch.LaunchError):
                    launch.check_flags(['/tmp/venv/bin/turboquant-serve','--kv-bits','8'])
                inspect.assert_not_called()

    def test_preflight_only_never_executes_model_or_opens_port(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            with mock.patch.object(launch.platform,'system',return_value='Darwin'), \
                 mock.patch.object(launch.platform,'machine',return_value='arm64'), \
                 mock.patch.object(launch,'check_snapshot',return_value=(Path(tmp),{'revision':'fixture','repo':'fixture'})), \
                 mock.patch.object(launch,'check_flags',return_value='synthetic help'), \
                 mock.patch.object(launch.os,'execvpe') as execute, \
                 mock.patch.object(launch.socket,'socket') as socket:
                result=launch.main(['qwen36-asym','--lab',tmp,'--accept-tight-memory','--preflight-only'])
                self.assertEqual(result,0)
                execute.assert_not_called();socket.assert_not_called()
                self.assertFalse((Path(tmp)/'standalone.lock').exists())
                self.assertTrue((Path(tmp)/'logs/qwen36-asym-preflight.json').exists())

    def test_metadata_probe_uses_selected_venv_without_importing_tq(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'venv'
            venv.EnvBuilder(with_pip=False).create(root)
            python=root/'bin/python'
            result=subprocess.run([str(python),'-I','-c','import sysconfig;print(sysconfig.get_path("purelib"))'],capture_output=True,text=True,check=True)
            site=Path(result.stdout.strip())
            package=site/'turboquant_mlx';package.mkdir()
            (package/'__init__.py').write_text('raise RuntimeError("MUST NOT IMPORT PACKAGE")\n')
            (package/'serve.py').write_text(source_fixture())
            dist=site/'turboquant_mlx_full-0.28.0.dist-info';dist.mkdir()
            (dist/'METADATA').write_text('Metadata-Version: 2.1\nName: turboquant-mlx-full\nVersion: 0.28.0\n')
            (dist/'entry_points.txt').write_text('[console_scripts]\nturboquant-serve = turboquant_mlx.serve:main\n')
            shim=root/'bin/turboquant-serve'
            shim.write_text(f'#!{python}\nfrom turboquant_mlx.serve import main\nmain()\n')
            report=launch.inspect_turboquant([str(shim)])
            self.assertEqual(report['version'],'0.28.0')
            self.assertEqual(report['registered_wrapper_flags'],launch.TQ_WRAPPER_PARSERS)
            self.assertNotIn('source',report)
            self.assertEqual(len(report['source_sha256']),64)


class WiredSnapshot(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)
        self.lab=self.base/'lab';self.lab.mkdir()
        self.bin=self.base/'bin';self.bin.mkdir()
        self.calls=self.base/'sysctl-calls'
        sysctl=self.bin/'sysctl'
        sysctl.write_text('#!/bin/bash\nprintf "%s\\n" "$*" >> "$CALLS"\n'
                          'if [ "$1" != -n ] || [ "$2" != iogpu.wired_limit_mb ]; then exit 99; fi\n'
                          'printf "%s\\n" "$FAKE_CURRENT"\nexit "${FAKE_STATUS:-0}"\n')
        sysctl.chmod(0o755)
        self.env={**os.environ,'PATH':str(self.bin)+':'+os.environ['PATH'],
                  'CALLS':str(self.calls),'FAKE_CURRENT':'12288'}
        self.saved=self.lab/'logs/wired_limit_before.txt'

    def tearDown(self):
        if self.calls.exists():
            self.assertTrue(all(line=='-n iogpu.wired_limit_mb' for line in self.calls.read_text().splitlines()))
        self.tmp.cleanup()

    def run_helper(self,action):
        return subprocess.run(['bash',str(ROOT/'scripts/wired_memory.sh'),action,str(self.lab)],
                              env=self.env,text=True,capture_output=True,timeout=5)

    def write_saved(self,value):
        self.saved.parent.mkdir(exist_ok=True)
        self.saved.write_text(value)

    def test_initial_snapshot(self):
        self.assertEqual(self.run_helper('save').returncode,0)
        self.assertEqual(self.saved.read_text(),'12288\n')
        self.assertEqual(self.saved.stat().st_mode & 0o777,0o600)

    def test_preserves_original_after_current_changes(self):
        self.write_saved('12288\n');self.env['FAKE_CURRENT']='13824'
        run=self.run_helper('save')
        self.assertEqual(run.returncode,0)
        self.assertEqual(self.saved.read_text(),'12288\n')
        self.assertIn('differ',run.stderr)

    def test_empty_snapshot_refused_not_replaced(self):
        self.write_saved('')
        self.assertNotEqual(self.run_helper('save').returncode,0)
        self.assertEqual(self.saved.read_text(),'')

    def test_non_numeric_snapshot_refused(self):
        self.write_saved('not a value')
        self.assertNotEqual(self.run_helper('saved-value').returncode,0)

    def test_zero_value_preserved(self):
        self.env['FAKE_CURRENT']='0'
        self.assertEqual(self.run_helper('save').returncode,0)
        self.assertEqual(self.run_helper('saved-value').stdout,'0\n')

    def test_failed_sysctl_never_creates_snapshot(self):
        self.env['FAKE_STATUS']='1'
        self.assertNotEqual(self.run_helper('save').returncode,0)
        self.assertFalse(self.saved.exists())

    def test_invalid_current_never_creates_snapshot(self):
        self.env['FAKE_CURRENT']=''
        self.assertNotEqual(self.run_helper('save').returncode,0)
        self.assertFalse(self.saved.exists())

    def test_symlink_snapshot_refused(self):
        self.saved.parent.mkdir()
        target=self.base/'unrelated';target.write_text('9999\n')
        self.saved.symlink_to(target)
        self.assertNotEqual(self.run_helper('save').returncode,0)
        self.assertEqual(target.read_text(),'9999\n')

    def test_saved_value_does_not_read_current(self):
        self.write_saved('12288\n')
        self.assertEqual(self.run_helper('saved-value').stdout,'12288\n')
        self.assertFalse(self.calls.exists())

    def test_status_does_not_create_file(self):
        self.assertEqual(self.run_helper('status').returncode,0)
        self.assertFalse(self.saved.exists())





if __name__=='__main__':unittest.main()
