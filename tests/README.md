# Merkle regression tests — VCP v1.1 examples

Run offline from the repository root with Python 3.10+ and Node.js 22.18+
(native TypeScript type stripping). No third-party Python or npm packages are
required. Node is required: the suite fails rather than silently skipping the
TypeScript example.

```bash
python -m unittest discover -s tests -v
```

The tests extract the actual Markdown code fences: both Python `MerkleTree`
classes in Implementation Guide §§3.3 and 9.1, the TypeScript class in §9.2, and
the README verifier. The complete README Quick Start also runs with mocked HTTP
responses. This prevents passing tests against a separate corrected copy while
leaving broken published examples behind.

## Frozen known values

`merkle_v1_1_vectors.json` contains literal expected roots for sizes 0–8 and
audit paths for every position in a three-leaf tree plus the final leaf of a
seven-leaf tree. Each event hash is 32 repetitions of its zero-based index byte:
`00…00`, `01…01`, …, `07…07`. These are synthetic leaf data, not claims about
real event hashes or canonicalization.

Values were calculated independently of the documentation implementation using
OpenSSL SHA-256 with hand-expanded tree expressions from
[RFC 6962 §§2.1–2.1.1](https://www.rfc-editor.org/rfc/rfc6962#section-2.1).
For `Li = SHA256(0x00 || event_hash_i)` and `N(a,b) = SHA256(0x01 || a || b)`:

| Size | Expression |
|---|---|
| 0 | `SHA256(empty)` |
| 1 | `L0` |
| 2 | `N(L0,L1)` |
| 3 | `N(N(L0,L1),L2)` |
| 4 | `N(N(L0,L1),N(L2,L3))` |
| 5 | `N(root4,L4)` |
| 6 | `N(root4,N(L4,L5))` |
| 7 | `N(root4,N(N(L4,L5),L6))` |
| 8 | `N(root4,N(N(L4,L5),N(L6,L7)))` |

For example, reproduce the three-leaf root without importing any example code:

```python
import subprocess

def h(data):
    return subprocess.run(
        ['openssl', 'dgst', '-sha256', '-binary'],
        input=data, capture_output=True, check=True,
    ).stdout

a, b, c = [h(b'\x00' + bytes([i]) * 32) for i in range(3)]
print(h(b'\x01' + h(b'\x01' + a + b) + c).hex())
```

The suite reads frozen values without regenerating them and also compares all
sizes 1–65 against an independent bottom-up implementation that promotes an
unpaired node unchanged. It checks every leaf's Python/TypeScript audit path
and verifies both languages' proofs with the README verifier (2,145 distinct
size/index combinations). It rejects malformed/truncated/extended paths,
invalid sibling directions and hash lengths, tampered data/roots/siblings,
and regressions to the former missing-prefix and duplicate-last algorithms.
It also checks single-leaf empty paths, empty-tree proof rejection, invalid
indices, reset, and non-mutating proof generation.

## Verification boundary

The proof verifier checks inclusion relative to the supplied expected root and
the proof's tree size. Sibling directions determine a path; this interface does
not attest to a separately supplied leaf index. A root hash alone does not
authenticate a claimed tree size: obtain and compare the size with a trusted
anchor/checkpoint when that claim matters. Production callers must authenticate
the expected root independently and recompute the event hash using applicable
canonicalization rules. The API demonstration checks internal consistency only.

This is a focused correction and regression suite for **v1.1 implementation
materials**. It does not validate the live Explorer API, event canonicalization,
signatures, external anchoring, other examples, or full VCP conformance. It makes
no VCP v1.2 conformance claim and leaves the historical v1.0 SDK document intact.
