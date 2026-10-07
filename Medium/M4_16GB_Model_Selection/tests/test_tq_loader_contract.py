"""Synthetic source fixtures: no MLX, TurboQuant, weights or network required."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_tq_loader_contract import check_sources, ContractError

TQ = '''
raise RuntimeError("MUST NOT EXECUTE THIS SOURCE")
def _patch_loader():
    def _tq_aware_load(path_or_hf_repo, tokenizer_config=None,
                       model_config=None, adapter_path=None, lazy=False,
                       return_config=False, revision=None):
        raise RuntimeError("MUST NOT LOAD WEIGHTS")
'''
SERVER = '''
raise RuntimeError("MUST NOT EXECUTE THIS SOURCE")
class ModelProvider:
    def _load(self, model_path, adapter_path=None, draft_model_path=None):
        result = load(model_path, adapter_path=adapter_path,
                      tokenizer_config=self._tokenizer_config)
        if draft_model_path:
            draft = load(draft_model_path)
'''

class LoaderContractTests(unittest.TestCase):
    def test_matching_legacy_call(self):
        result = check_sources(SERVER, TQ)
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['checked_calls']), 2)
    def test_exact_reported_failure(self):
        changed = SERVER.replace('tokenizer_config=self._tokenizer_config)',
                                 'tokenizer_config=self._tokenizer_config, trust_remote_code=False)')
        with self.assertRaisesRegex(ContractError, 'trust_remote_code'):
            check_sources(changed, TQ)
    def test_true_not_solution(self):
        changed = SERVER.replace('tokenizer_config=self._tokenizer_config)',
                                 'tokenizer_config=self._tokenizer_config, trust_remote_code=True)')
        with self.assertRaisesRegex(ContractError, 'trust_remote_code'):
            check_sources(changed, TQ)
    def test_nested_tokenizer_setting_is_not_top_level_argument(self):
        changed = SERVER.replace('self._tokenizer_config)', '{"trust_remote_code": False})')
        self.assertTrue(check_sources(changed, TQ)['passed'])
    def test_extra_unknown_kw(self):
        changed = SERVER.replace('tokenizer_config=self._tokenizer_config)', 'future_option=1)')
        with self.assertRaisesRegex(ContractError, 'future_option'):
            check_sources(changed, TQ)
    def test_compatible_explicit_future_wrapper(self):
        wrapper = TQ.replace('revision=None):', 'revision=None, trust_remote_code=False):')
        changed = SERVER.replace('tokenizer_config=self._tokenizer_config)',
                                 'tokenizer_config=self._tokenizer_config, trust_remote_code=False)')
        self.assertTrue(check_sources(changed, wrapper)['passed'])
    def test_dynamic_kwargs_refused(self):
        changed = SERVER.replace('tokenizer_config=self._tokenizer_config)', '**extras)')
        with self.assertRaisesRegex(ContractError, 'Dynamic'):
            check_sources(changed, TQ)
    def test_dynamic_args_refused(self):
        with self.assertRaisesRegex(ContractError, 'Dynamic'):
            check_sources(SERVER.replace('load(model_path,', 'load(*paths,'), TQ)
    def test_missing_model_provider(self):
        with self.assertRaisesRegex(ContractError, 'ModelProvider'):
            check_sources(SERVER.replace('ModelProvider', 'Other'), TQ)
    def test_missing_wrapper(self):
        with self.assertRaisesRegex(ContractError, '_tq_aware_load'):
            check_sources(SERVER, TQ.replace('_tq_aware_load', '_other'))
    def test_missing_call(self):
        with self.assertRaisesRegex(ContractError, 'No bare load'):
            check_sources(SERVER.replace('load(', 'other(').replace('def _other', 'def _load'), TQ)
    def test_invalid_source(self):
        with self.assertRaisesRegex(ContractError, 'source layout'):
            check_sources('def broken(:', TQ)
    def test_missing_required_parameter(self):
        wrapper = TQ.replace('tokenizer_config=None,', 'required_extra, tokenizer_config=None,')
        with self.assertRaisesRegex(ContractError, 'required_extra'):
            check_sources(SERVER, wrapper)
    def test_too_many_positionals(self):
        changed = SERVER.replace('load(draft_model_path)', 'load(1,2,3,4,5,6,7,8)')
        with self.assertRaisesRegex(ContractError, 'too many positional'):
            check_sources(changed, TQ)
    def test_source_not_executed(self):
        result=check_sources(SERVER,TQ)
        self.assertFalse(result['native_modules_imported'])
        self.assertFalse(result['models_loaded'])

if __name__=='__main__':
    unittest.main()
