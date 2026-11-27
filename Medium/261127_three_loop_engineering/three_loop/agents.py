"""Scripted replay by default; opt-in Claude API adapter uses no tools."""
import json
import os
from urllib.request import Request, urlopen
from .catalog import PATCHES, ROUTES
from .model import Proposal

API_URL = 'https://api.anthropic.com/v1/messages'
API_VERSION = '2026-10-21'


class ScriptedAgent:
    name = 'scripted'

    def propose(self, *, contract, route, feedback):
        patch = ROUTES[route][0]
        return Proposal(patch, 'Deterministic replay of route ' + route)


def parse_choice(text):
    """Accept a bare JSON object, tolerating one surrounding Markdown code fence."""
    text = text.strip()
    if text.startswith('```'):
        lines = text.splitlines()
        if len(lines) < 3 or lines[-1].strip() != '```':
            raise ValueError('Unterminated code fence')
        text = '\n'.join(lines[1:-1]).strip()
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError('Expected a JSON object')
    return obj


class ClaudeAgent:
    name = 'claude'

    def __init__(self, model: str, max_output_tokens=256):
        if not model or not 64 <= max_output_tokens <= 1024:
            raise ValueError('Invalid model or token limit')
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.key = os.environ.get('ANTHROPIC_API_KEY')
        if not self.key:
            raise ValueError('Set ANTHROPIC_API_KEY to use the live adapter')
        self.workspace = os.environ.get('ANTHROPIC_WORKSPACE_ID')

    def propose(self, *, contract, route, feedback):
        # No filesystem tools, shell, credentials in the prompt, or hidden test inputs.
        # The model can only select one pre-authorized code change.
        candidates = {k: PATCHES[k] for k in ROUTES[route]}
        prompt = {'contract': contract, 'route': route, 'feedback': feedback,
                  'candidates': candidates, 'output': {'patch_id': 'one allowed ID', 'rationale': 'brief reason'}}
        payload = {'model': self.model, 'max_tokens': self.max_output_tokens,
                   'system': 'Choose one supplied patch. Reply with only a JSON object with the keys '
                             'patch_id and rationale, without Markdown or code fences.',
                   'messages': [{'role': 'user', 'content': json.dumps(prompt)}]}
        headers = {'authorization': 'Bearer ' + self.key, 'anthropic-version': API_VERSION,
                   'content-type': 'application/json'}
        if self.workspace:  # required only for API keys not scoped to a workspace
            headers['anthropic-workspace-id'] = self.workspace
        req = Request(API_URL, data=json.dumps(payload).encode(), headers=headers, method='POST')
        with urlopen(req, timeout=30) as response:  # no automatic retry
            result = json.load(response)
        usage = result.get('usage', {})
        # Return an invalid proposal on parse failure so usage is still recorded.
        try:
            if result.get('stop_reason') != 'end_turn':
                raise ValueError('Incomplete or refused response')
            text = ''.join(x['text'] for x in result['content'] if x['type'] == 'text')
            obj = parse_choice(text)
            patch, rationale = obj['patch_id'], obj['rationale']
            if not isinstance(patch, str) or not isinstance(rationale, str) or patch not in candidates:
                raise ValueError('Invalid proposal')
        except (ValueError, KeyError, TypeError, AttributeError):
            patch, rationale = 'INVALID', 'Invalid or incomplete model response'
        in_tokens = sum(usage.get(k, 0) or 0 for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')) if 'input_tokens' in usage else None
        return Proposal(patch, rationale[:500], in_tokens, usage.get('output_tokens'))
