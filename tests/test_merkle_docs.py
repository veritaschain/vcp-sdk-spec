"""Execute the published v1.1 examples, not a separate implementation copy."""

import ast
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
GUIDE = (ROOT / 'VCP_IMPLEMENTATION_GUIDE_v1_1.md').read_text()
README = (ROOT / 'README.md').read_text()
VECTORS = json.loads((ROOT / 'tests/merkle_v1_1_vectors.json').read_text())


def blocks(document, language):
    return re.findall(r'^```' + language + r'\n(.*?)^```', document, re.M | re.S)


def python_definition(code, name):
    """Isolate a class/function without executing unrelated demo side effects."""
    node, = [node for node in ast.parse(code).body
             if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == name]
    namespace = {'hashlib': hashlib}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<doc example>', 'exec'), namespace)
    return namespace[name]


QUICKSTART, = [code for code in blocks(README, 'python') if 'def verify_merkle_proof' in code]
VERIFY = python_definition(QUICKSTART, 'verify_merkle_proof')
TREES = [python_definition(code, 'MerkleTree') for code in blocks(GUIDE, 'python')
         if 'class MerkleTree:' in code]
TS_CODE, = [code for code in blocks(GUIDE, 'typescript') if 'class MerkleTree {' in code]
EVENTS = [(bytes([i]) * 32).hex() for i in range(65)]


def reference_root(events):
    """Independent bottom-up oracle: promote an unpaired node unchanged."""
    nodes = [hashlib.sha256(b'\x00' + bytes.fromhex(event)).digest() for event in events]
    if not nodes:
        return hashlib.sha256(b'').hexdigest()
    while len(nodes) > 1:
        nodes = [hashlib.sha256(b'\x01' + nodes[i] + nodes[i + 1]).digest()
                 if i + 1 < len(nodes) else nodes[i] for i in range(0, len(nodes), 2)]
    return nodes[0].hex()


def duplicate_last_root(events):
    nodes = [hashlib.sha256(b'\x00' + bytes.fromhex(event)).digest() for event in events]
    while len(nodes) > 1:
        if len(nodes) % 2:
            nodes.append(nodes[-1])
        nodes = [hashlib.sha256(b'\x01' + nodes[i] + nodes[i + 1]).digest()
                 for i in range(0, len(nodes), 2)]
    return nodes[0].hex()


def build(tree_class, events):
    tree = tree_class()
    for event in events:
        tree.add(event)
    return tree


def envelope(tree, events, index):
    return {'event_hash': events[index], 'merkle_root': tree.root(),
            'tree_size': len(events), 'proof_path': tree.proof(index)}


class MerkleDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Node 22.18+ runs erasable TypeScript directly. No npm dependencies.
        # Extract the published class, leaving the unrelated VCP client out.
        source = TS_CODE.split('interface VCPEvent')[0]
        source += TS_CODE[TS_CODE.index('class MerkleTree {'):TS_CODE.index('class VCPClient {')]
        source += '''
import assert from 'node:assert/strict';
const events = Array.from({length: 65}, (_, i) => Buffer.alloc(32, i).toString('hex'));
const results = [];
for (let size = 0; size <= events.length; size++) {
  const tree = new MerkleTree();
  events.slice(0, size).forEach(event => tree.add(event));
  const root = tree.root();
  const paths = events.slice(0, size).map((_, index) => tree.proof(index));
  assert.equal(tree.root(), root); // proof generation must not mutate the tree
  for (const index of [-1, size, 0.5, NaN]) assert.throws(() => tree.proof(index));
  tree.reset();
  assert.equal(tree.root(), createHash('sha256').update(Buffer.alloc(0)).digest('hex'));
  assert.throws(() => tree.proof(0));
  results.push({root, paths});
}
for (const bad of ['', '00', '0'.repeat(63), '0'.repeat(65), 'g'.repeat(64), ' '.repeat(64),
                   '0'.repeat(64) + String.fromCharCode(10)]) {
  assert.throws(() => new MerkleTree().add(bad));
}
const upper = new MerkleTree();
upper.add('AB'.repeat(32));
assert.equal(upper.root(), createHash('sha256').update(Buffer.concat([
  Buffer.from([0]), Buffer.alloc(32, 0xab)
])).digest('hex'));
process.stdout.write(JSON.stringify(results));
'''
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / 'merkle-doc-test.mts'
            script.write_text(source)
            output = subprocess.run(['node', str(script)], capture_output=True, text=True, check=True)
        cls.ts_results = json.loads(output.stdout)

    def test_all_documented_tree_implementations_are_exercised(self):
        self.assertEqual(len(TREES), 2)
        self.assertEqual(len(self.ts_results), 66)

    def test_frozen_known_roots(self):
        for size_text, expected in VECTORS['roots'].items():
            size = int(size_text)
            events = VECTORS['event_hashes'][:size]
            with self.subTest(size=size):
                self.assertEqual(reference_root(events), expected)
                self.assertEqual(self.ts_results[size]['root'], expected)
                for tree_class in TREES:
                    self.assertEqual(build(tree_class, events).root(), expected)

    def test_frozen_audit_paths(self):
        for vector in VECTORS['proofs']:
            size, index = vector['tree_size'], vector['index']
            with self.subTest(size=size, index=index):
                self.assertEqual(self.ts_results[size]['paths'][index], vector['proof_path'])
                for tree_class in TREES:
                    tree = build(tree_class, EVENTS[:size])
                    self.assertEqual(tree.proof(index), vector['proof_path'])
                proof = {'event_hash': EVENTS[index], 'merkle_root': VECTORS['roots'][str(size)],
                         'tree_size': size, 'proof_path': vector['proof_path']}
                self.assertTrue(VERIFY(proof, EVENTS[index], VECTORS['roots'][str(size)]))

    def test_all_positions_sizes_1_through_65_cross_language(self):
        for size in range(1, 66):
            events = EVENTS[:size]
            expected = reference_root(events)
            self.assertEqual(self.ts_results[size]['root'], expected)
            for tree_class in TREES:
                tree = build(tree_class, events)
                self.assertEqual(tree.root(), expected)
                for index, event in enumerate(events):
                    with self.subTest(size=size, index=index, implementation=tree_class):
                        proof = envelope(tree, events, index)
                        self.assertTrue(VERIFY(proof, event, expected))
                        self.assertEqual(proof['proof_path'], self.ts_results[size]['paths'][index])
                        proof['proof_path'] = self.ts_results[size]['paths'][index]
                        self.assertTrue(VERIFY(proof, event, expected))
                self.assertEqual(tree.root(), expected)

    def test_empty_and_single_leaf(self):
        for tree_class in TREES:
            tree = tree_class()
            with self.assertRaises(ValueError):
                tree.proof(0)
            empty = {'event_hash': EVENTS[0], 'merkle_root': tree.root(), 'tree_size': 0, 'proof_path': []}
            self.assertFalse(VERIFY(empty, EVENTS[0], tree.root()))
            tree.add(EVENTS[0])
            self.assertEqual(tree.proof(0), [])
            self.assertNotEqual(tree.root(), EVENTS[0])
            self.assertTrue(VERIFY(envelope(tree, EVENTS[:1], 0), EVENTS[0], tree.root()))
            tree.reset()
            self.assertEqual(tree.root(), VECTORS['roots']['0'])
            tree.add(EVENTS[1])
            self.assertEqual(tree.root(), reference_root(EVENTS[1:2]))

    def test_invalid_tree_inputs(self):
        for tree_class in TREES:
            tree = build(tree_class, EVENTS[:3])
            for bad in ['', '00', '0' * 63, '0' * 65, 'g' * 64, ' ' * 64, None, 12]:
                with self.subTest(bad=bad), self.assertRaises((ValueError, TypeError)):
                    tree.add(bad)
            for bad in [-1, 3, 0.5, True, '0', None]:
                with self.subTest(index=bad), self.assertRaises(ValueError):
                    tree.proof(bad)
            self.assertEqual(tree.root(), VECTORS['roots']['3'])
            self.assertEqual(build(tree_class, ['AB' * 32]).root(), reference_root(['ab' * 32]))

    def test_tampering_and_malformed_proofs_rejected(self):
        tree = build(TREES[0], EVENTS[:7])
        valid = envelope(tree, EVENTS[:7], 0)
        corruptions = []
        for key in valid:
            broken = copy.deepcopy(valid)
            del broken[key]
            corruptions.append(broken)
        for field in ['event_hash', 'merkle_root']:
            for value in ['ff' * 32, 'aa' * 31, 'gg' * 32, None, 123]:
                broken = copy.deepcopy(valid)
                broken[field] = value
                corruptions.append(broken)
        for size in [0, -1, 1, 2, 4, True, 7.0, '7', None]:
            broken = copy.deepcopy(valid)
            broken['tree_size'] = size
            corruptions.append(broken)
        for path in [None, {}, [], valid['proof_path'][:-1], valid['proof_path'][1:],
                     valid['proof_path'] + [valid['proof_path'][0]], list(reversed(valid['proof_path']))]:
            broken = copy.deepcopy(valid)
            broken['proof_path'] = path
            corruptions.append(broken)
        for index in range(len(valid['proof_path'])):
            for field, value in [('position', 'left'), ('position', 'other'), ('position', None),
                                 ('hash', 'ff' * 32), ('hash', 'aa' * 31), ('hash', 'gg' * 32)]:
                broken = copy.deepcopy(valid)
                broken['proof_path'][index][field] = value
                corruptions.append(broken)
        for step in [None, {}, 'bad', {'hash': EVENTS[1]}, {'position': 'right'}]:
            broken = copy.deepcopy(valid)
            broken['proof_path'][0] = step
            corruptions.append(broken)
        for broken in corruptions + [None, [], 'invalid']:
            with self.subTest(proof=broken):
                self.assertFalse(VERIFY(broken, EVENTS[0], tree.root()))
        self.assertFalse(VERIFY(valid, EVENTS[1], tree.root()))
        self.assertFalse(VERIFY(valid, EVENTS[0], 'ff' * 32))

    def test_domain_separation_and_duplicate_last_regressions(self):
        for size in [3, 5, 6, 7]:
            old_root = duplicate_last_root(EVENTS[:size])
            self.assertNotEqual(old_root, VECTORS['roots'][str(size)])
            tree = build(TREES[0], EVENTS[:size])
            proof = envelope(tree, EVENTS[:size], size - 1)
            proof['merkle_root'] = old_root
            self.assertFalse(VERIFY(proof, EVENTS[size - 1], old_root))
        tree = build(TREES[0], EVENTS[:3])
        proof = envelope(tree, EVENTS[:3], 0)
        for leaf_prefix, node_prefix in [(b'', b''), (b'', b'\x01'), (b'\x00', b'')]:
            # Legacy README used the raw event hash as the initial value.
            current = (hashlib.sha256(leaf_prefix + bytes.fromhex(EVENTS[0])).digest()
                       if leaf_prefix else bytes.fromhex(EVENTS[0]))
            for step in proof['proof_path']:
                current = hashlib.sha256(node_prefix + current + bytes.fromhex(step['hash'])).digest()
            bad = dict(proof, merkle_root=current.hex())
            self.assertFalse(VERIFY(bad, EVENTS[0], current.hex()))
        # Supplying a pre-prefixed leaf as event data must not match the true root.
        leaf_hash = hashlib.sha256(b'\x00' + bytes.fromhex(EVENTS[0])).hexdigest()
        self.assertFalse(VERIFY(dict(proof, event_hash=leaf_hash), leaf_hash, tree.root()))

    def test_complete_readme_quickstart_offline(self):
        tree = build(TREES[0], EVENTS[:3])
        proof = envelope(tree, EVENTS[:3], 2)
        event = {'header': {'event_type': 'SIG', 'symbol': 'XAUUSD', 'event_id': 'test-event'},
                 'security': {'event_hash': EVENTS[2]}}

        class Response:
            def __init__(self, payload):
                self.payload = payload

            def json(self):
                return self.payload

            def raise_for_status(self):
                pass

        fake = types.ModuleType('httpx')
        fake.get = lambda url, **kwargs: Response(proof if url.endswith('/proof') else {'events': [event]})
        for tampered in [False, True]:
            if tampered:
                proof['proof_path'][0]['hash'] = 'ff' * 32
            output = io.StringIO()
            with patch.dict(sys.modules, {'httpx': fake}), contextlib.redirect_stdout(output):
                exec(compile(QUICKSTART, '<README quickstart>', 'exec'), {'__name__': '__test__'})
            self.assertIn('FAILED' if tampered else 'MATCH', output.getvalue())


if __name__ == '__main__':
    unittest.main()
