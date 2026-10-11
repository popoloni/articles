"""R3 L6 regressions use synthetic runtime evidence only; no inference."""
from pathlib import Path
import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import launch_lab as launch
from test_l5_r3 import source_fixture

class StreamingRegression(unittest.TestCase):
    def test_three_reported_hidden_flags_preserved(self):
        cmd=launch.command('qwen36-stream','/tmp/lab')
        before=list(cmd)
        help_text=' '.join(launch.flags_in_command(cmd)-launch.TQ_WRAPPER_PARSERS.keys())
        evidence=launch.wrapper_flags_from_source(source_fixture())
        launch.validate_flags(cmd,help_text,evidence)
        self.assertEqual(cmd,before)
        for flag in ('--cache-budget-gb','--max-active-experts','--tool-syntax-greedy'):
            self.assertIn(flag,cmd)
        self.assertEqual(cmd[cmd.index('--cache-budget-gb')+1],'4')
        self.assertEqual(cmd[cmd.index('--max-active-experts')+1],'0')
        self.assertEqual(cmd[cmd.index('--kv-bits')+1],'8')

    def test_missing_cache_trigger_fails_instead_of_resident_fallback(self):
        cmd=launch.command('qwen36-stream','/tmp/lab')
        evidence=dict(launch.TQ_WRAPPER_PARSERS);del evidence['--cache-budget-gb']
        with self.assertRaisesRegex(launch.LaunchError,'cache-budget-gb'):
            launch.validate_flags(cmd,' '.join(cmd),evidence)

    def test_missing_routing_flag_fails_instead_of_k_reduction(self):
        cmd=launch.command('qwen36-stream','/tmp/lab')
        evidence=dict(launch.TQ_WRAPPER_PARSERS);del evidence['--max-active-experts']
        with self.assertRaisesRegex(launch.LaunchError,'max-active-experts'):
            launch.validate_flags(cmd,' '.join(cmd),evidence)

    def test_stream_preflight_has_no_socket_or_model_load(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            with mock.patch.object(launch.platform,'system',return_value='Darwin'), \
                 mock.patch.object(launch.platform,'machine',return_value='arm64'), \
                 mock.patch.object(launch,'check_snapshot',return_value=(Path(tmp),{'revision':'fixture','repo':'fixture'})), \
                 mock.patch.object(launch,'check_flags',return_value='synthetic help'), \
                 mock.patch.object(launch.os,'execvpe') as execute, \
                 mock.patch.object(launch.socket,'socket') as socket:
                self.assertEqual(launch.main(['qwen36-stream','--lab',tmp,'--expert-cache-gb','4','--preflight-only']),0)
                execute.assert_not_called();socket.assert_not_called()
                self.assertTrue((Path(tmp)/'logs/qwen36-stream-preflight.json').is_file())
                self.assertFalse((Path(tmp)/'standalone.lock').exists())

    def test_failed_preflight_writes_report_does_not_start(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with mock.patch.object(launch.platform,'system',return_value='Darwin'), \
                 mock.patch.object(launch.platform,'machine',return_value='arm64'), \
                 mock.patch.object(launch,'check_snapshot',return_value=(Path(tmp),{'revision':'fixture','repo':'fixture'})), \
                 mock.patch.object(launch,'check_flags',side_effect=launch.LaunchError('missing fixture flag')), \
                 mock.patch.object(launch.os,'execvpe') as execute:
                self.assertEqual(launch.main(['qwen36-stream','--lab',tmp,'--preflight-only']),2)
                execute.assert_not_called()
                self.assertIn('missing fixture flag',json.loads((Path(tmp)/'logs/qwen36-stream-preflight.json').read_text())['error'])



if __name__=='__main__':unittest.main()
