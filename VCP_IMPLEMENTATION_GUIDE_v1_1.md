# VCP Implementation Guide v1.1

**Document ID:** VSO-IMPL-001  
**Status:** Production Ready  
**Version:** 1.1.0  
**Date:** 2025-12-30  
**Maintainer:** VeritasChain Standards Organization (VSO)  
**License:** Apache 2.0

---

**Merkle erratum (2026-10-08):** The Python and TypeScript Merkle examples now
use RFC 6962 §§2.1–2.1.1 for empty roots, unbalanced trees, and audit paths.
This correction is scoped to **VCP v1.1 implementation materials**; it neither
upgrades this guide to VCP v1.2 nor claims verified VCP v1.2 conformance.
The regression tests validate the Merkle examples, not this guide's other
illustrative code or full protocol conformance.

## Table of Contents

1. [Overview](#1-overview)
2. [What's New in v1.1](#2-whats-new-in-v11)
3. [Three-Layer Architecture](#3-three-layer-architecture)
4. [Quick Start by Tier](#4-quick-start-by-tier)
5. [External Anchoring](#5-external-anchoring)
6. [Policy Identification](#6-policy-identification)
7. [Error Event Standardization](#7-error-event-standardization)
8. [VCP-XREF Dual Logging](#8-vcp-xref-dual-logging)
9. [Complete Code Examples](#9-complete-code-examples)
10. [Migration from v1.0](#10-migration-from-v10)
11. [Conformance Testing](#11-conformance-testing)
12. [Sidecar Deployment](#12-sidecar-deployment)
13. [Appendices](#13-appendices)

---

## 1. Overview

### 1.1 Purpose

This guide provides practical implementation guidance for VCP v1.1. It covers:

- Three-layer integrity architecture
- Mandatory external anchoring for all tiers
- Policy Identification requirements
- Code examples in Python, TypeScript, and MQL5

### 1.2 Target Audience

- Software engineers implementing VCP
- System architects designing audit infrastructure
- DevOps engineers deploying VCP sidecars
- QA engineers validating conformance

### 1.3 Prerequisites

- Understanding of SHA-256 hashing
- Familiarity with Merkle trees (RFC 6962)
- Basic knowledge of Ed25519 signatures

### 1.4 Conformance Keywords

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHOULD", "RECOMMENDED", "MAY", and "OPTIONAL" follow RFC 2119.

---

## 2. What's New in v1.1

### 2.1 Change Summary

| Feature | v1.0 | v1.1 | Action Required |
|---------|------|------|-----------------|
| External Anchor (Silver) | OPTIONAL | **REQUIRED** | Implementation |
| PrevHash (Hash Chain) | REQUIRED | **OPTIONAL** | None |
| Policy Identification | N/A | **REQUIRED** | Implementation |
| VCP-XREF | N/A | OPTIONAL | None |
| Error Events | Ad-hoc | Standardized | Schema update |

### 2.2 Protocol Compatibility

**v1.1 is fully backward compatible with v1.0.**

Existing v1.0 logs can be read and verified by v1.1 systems.

### 2.3 Certification Deadlines

| Requirement | Deadline |
|-------------|----------|
| Policy Identification | 2026-03-25 |
| External Anchor (Silver) | 2026-06-25 |

---

## 3. Three-Layer Architecture

### 3.1 Overview

VCP v1.1 defines a clear three-layer architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  LAYER 3: External Verifiability                                    │
│  ─────────────────────────────────                                  │
│  Purpose: Third-party verification without trusting producer        │
│                                                                     │
│  Components:                                                        │
│  ├─ Digital Signature (Ed25519): REQUIRED                          │
│  ├─ Timestamp (ISO + int64): REQUIRED                              │
│  └─ External Anchor: REQUIRED ← v1.1 mandatory for ALL tiers       │
│                                                                     │
│  Frequency: Platinum 10min / Gold 1hr / Silver 24hr                │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYER 2: Collection Integrity                                      │
│  ──────────────────────────────                                     │
│  Purpose: Prove completeness of event batches                       │
│                                                                     │
│  Components:                                                        │
│  ├─ Merkle Tree (RFC 6962): REQUIRED                               │
│  ├─ Merkle Root: REQUIRED                                          │
│  └─ Audit Path: REQUIRED                                           │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYER 1: Event Integrity                                           │
│  ─────────────────────────                                          │
│  Purpose: Individual event integrity                                │
│                                                                     │
│  Components:                                                        │
│  ├─ EventHash (SHA-256): REQUIRED                                  │
│  └─ PrevHash (hash chain): OPTIONAL ← v1.1 relaxation              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Layer 1: Event Integrity

Each event MUST have an `event_hash`:

```python
import hashlib
import json

def compute_event_hash(event: dict) -> str:
    """
    Compute EventHash per VCP v1.1.
    
    Steps:
    1. Extract header + payload (exclude security)
    2. Canonicalize JSON (RFC 8785)
    3. SHA-256 hash
    """
    hashable = {
        "header": event["header"],
        "payload": event["payload"]
    }
    
    # RFC 8785 canonicalization (simplified)
    canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'))
    
    return hashlib.sha256(canonical.encode()).hexdigest()
```

**PrevHash (OPTIONAL in v1.1):**

```python
# v1.0: REQUIRED
# v1.1: OPTIONAL - use when real-time detection is needed

security = {
    "event_hash": event_hash,
    "prev_hash": previous_event_hash  # OPTIONAL
}
```

### 3.3 Layer 2: Collection Integrity

Events are batched using [RFC 6962 §2.1 and §2.1.1](https://www.rfc-editor.org/rfc/rfc6962#section-2.1).
For these SHA-256 examples, leaf data is the decoded 32-byte `event_hash`:

- Empty root: `SHA256(b"")`, not 32 zero bytes.
- Single leaf: `SHA256(0x00 || event_hash_bytes)`.
- Internal node: `SHA256(0x01 || left_subtree_root || right_subtree_root)`.
- For `n > 1`, split at the largest power of two **strictly less than `n`**.
  Never duplicate an unpaired leaf or subtree.

`proof(index)` implements the same recursive partition for audit paths. It
returns bottom-up sibling hashes; `position` names the sibling's side.
A single leaf has an empty path; an empty tree has no inclusion proof.
The examples store prefixed leaf hashes internally; callers pass unprefixed
event hashes to `add()` and the [README verifier](./README.md#python-example-direct-api-call).
Existing roots made by the former zero-root/duplicate-last algorithm are not
RFC 6962 roots for the affected sizes. Preserve historical evidence with its
original algorithm identified; do not silently relabel or overwrite anchors.

The class below is also repeated in §9.1 so that example remains self-contained:

```python
import hashlib


class MerkleTree:
    """RFC 6962 tree over decoded 32-byte event hashes (v1.1 example)."""

    def __init__(self):
        self.leaves: list[bytes] = []

    def add(self, event_hash: str):
        """Hash the event-hash bytes as leaf data, exactly once."""
        if not isinstance(event_hash, str) or len(event_hash) != 64:
            raise ValueError("event_hash must be 64 hexadecimal characters")
        data = bytes.fromhex(event_hash)
        if len(data) != 32:
            raise ValueError("event_hash must encode exactly 32 bytes")
        self.leaves.append(hashlib.sha256(b'\x00' + data).digest())

    def _root(self, start: int, size: int) -> bytes:
        if size == 0:
            return hashlib.sha256(b'').digest()
        if size == 1:
            return self.leaves[start]
        # Largest power of two strictly smaller than size (RFC 6962 §2.1).
        k = 1 << ((size - 1).bit_length() - 1)
        return hashlib.sha256(
            b'\x01' + self._root(start, k) + self._root(start + k, size - k)
        ).digest()

    def root(self) -> str:
        return self._root(0, len(self.leaves)).hex()

    def proof(self, index: int) -> list[dict[str, str]]:
        """Bottom-up audit path; position describes the sibling's side."""
        if type(index) is not int or not 0 <= index < len(self.leaves):
            raise ValueError("leaf index out of range")

        def path(start: int, size: int, offset: int) -> list[dict[str, str]]:
            if size == 1:
                return []
            k = 1 << ((size - 1).bit_length() - 1)
            if offset < k:
                return path(start, k, offset) + [{
                    "hash": self._root(start + k, size - k).hex(),
                    "position": "right",
                }]
            return path(start + k, size - k, offset - k) + [{
                "hash": self._root(start, k).hex(),
                "position": "left",
            }]

        return path(0, len(self.leaves), index)

    def reset(self):
        self.leaves = []
```

For a batch of event hashes, generate a proof accepted by the README verifier:

```python
event_hashes = ["00" * 32, "01" * 32, "02" * 32]
tree = MerkleTree()
for event_hash in event_hashes:
    tree.add(event_hash)
index = 2
proof = {
    "event_hash": event_hashes[index],
    "merkle_root": tree.root(),
    "tree_size": len(event_hashes),
    "proof_path": tree.proof(index),
}
# The last leaf of a three-leaf tree has ONE sibling: the first-two-leaf root.
# verify_merkle_proof(proof, event_hashes[index], tree.root()) returns True.
# Independently authenticate the expected root and tree size in production.
```

### 3.4 Layer 3: External Verifiability

**REQUIRED for all tiers in v1.1.**

| Tier | Frequency | Recommended Anchor |
|------|-----------|-------------------|
| Platinum | 10 minutes | Ethereum, RFC 3161 TSA |
| Gold | 1 hour | RFC 3161 TSA |
| Silver | 24 hours | OpenTimestamps (FREE) |

---

## 4. Quick Start by Tier

### 4.1 Silver Tier (MT4/MT5/Retail)

**Requirements:**

```yaml
Clock Sync: BEST_EFFORT
Timestamp: MILLISECOND
Signature: Delegated or Ed25519
External Anchor: REQUIRED - Daily
Hash Chain: OPTIONAL
```

**Minimal Implementation:**

```python
from datetime import datetime, timezone
import uuid
import hashlib
import json

class VCPSilverClient:
    def __init__(self, policy_id: str):
        self.policy_id = policy_id
        self.tree = MerkleTree()
        self.events = []
    
    def log(self, event_type: str, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        
        event = {
            "header": {
                "event_id": str(uuid.uuid4()),
                "event_type": event_type,
                "timestamp_iso": now.isoformat(),
                "timestamp_int": str(int(now.timestamp() * 1000)),
                "timestamp_precision": "MILLISECOND",
                "clock_sync_status": "BEST_EFFORT",
                "vcp_version": "1.1",
                "hash_algo": "SHA256"
            },
            "payload": payload,
            "policy_identification": {
                "version": "1.1",
                "policy_id": self.policy_id,
                "conformance_tier": "SILVER"
            }
        }
        
        event_hash = self._compute_hash(event)
        event["security"] = {"event_hash": event_hash}
        
        self.tree.add(event_hash)
        self.events.append(event)
        
        return event
    
    def _compute_hash(self, event: dict) -> str:
        hashable = {"header": event["header"], "payload": event["payload"]}
        canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def anchor(self) -> dict:
        """Daily anchor - REQUIRED in v1.1."""
        root = self.tree.root()
        
        # Use OpenTimestamps (free)
        # pip install opentimestamps-client
        import opentimestamps
        timestamp = opentimestamps.stamp(bytes.fromhex(root))
        
        result = {
            "merkle_root": root,
            "event_count": len(self.events),
            "anchored_at": datetime.now(timezone.utc).isoformat(),
            "anchor_type": "OPENTIMESTAMPS"
        }
        
        # Reset for next batch
        self.tree = MerkleTree()
        self.events = []
        
        return result
```

### 4.2 Gold Tier (Prop Firms/Institutional)

**Requirements:**

```yaml
Clock Sync: NTP_SYNCED
Timestamp: MICROSECOND
Signature: Ed25519 (self-signing)
External Anchor: REQUIRED - Hourly
Hash Chain: RECOMMENDED
```

**Key Additions:**

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

class VCPGoldClient(VCPSilverClient):
    def __init__(self, policy_id: str, private_key: Ed25519PrivateKey):
        super().__init__(policy_id)
        self.private_key = private_key
        self.prev_hash = None
    
    def log(self, event_type: str, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        
        event = {
            "header": {
                "event_id": str(uuid.uuid4()),
                "event_type": event_type,
                "timestamp_iso": now.isoformat(),
                "timestamp_int": str(int(now.timestamp() * 1_000_000)),
                "timestamp_precision": "MICROSECOND",
                "clock_sync_status": "NTP_SYNCED",
                "vcp_version": "1.1",
                "hash_algo": "SHA256",
                "sign_algo": "ED25519"
            },
            "payload": payload,
            "policy_identification": {
                "version": "1.1",
                "policy_id": self.policy_id,
                "conformance_tier": "GOLD"
            }
        }
        
        event_hash = self._compute_hash(event)
        signature = self.private_key.sign(bytes.fromhex(event_hash)).hex()
        
        security = {
            "event_hash": event_hash,
            "signature": signature,
            "sign_algo": "ED25519"
        }
        
        # Hash chain (RECOMMENDED for Gold)
        if self.prev_hash:
            security["prev_hash"] = self.prev_hash
        
        event["security"] = security
        self.prev_hash = event_hash
        
        self.tree.add(event_hash)
        return event
```

### 4.3 Platinum Tier (HFT/Exchanges)

**Requirements:**

```yaml
Clock Sync: PTP_LOCKED (<1μs)
Timestamp: NANOSECOND
Signature: HSM recommended
External Anchor: REQUIRED - Every 10 min
Hash Chain: RECOMMENDED
Performance: >1M events/sec
```

> Platinum tier requires specialized infrastructure. See VSO-IMPL-PLATINUM-001.

---

## 5. External Anchoring

### 5.1 Anchor Targets

| Tier | Recommended | Alternative | Cost |
|------|-------------|-------------|------|
| Silver | OpenTimestamps | FreeTSA | FREE |
| Gold | RFC 3161 TSA | Certified DB | $-$$ |
| Platinum | Ethereum | RFC 3161 TSA | $$-$$$ |

### 5.2 OpenTimestamps (Silver Tier)

```bash
pip install opentimestamps-client
```

```python
import opentimestamps

def anchor_opentimestamps(merkle_root: str) -> dict:
    """
    Anchor to Bitcoin via OpenTimestamps.
    FREE service - no API key required.
    """
    root_bytes = bytes.fromhex(merkle_root)
    timestamp = opentimestamps.stamp(root_bytes)
    
    # Save proof file
    proof_path = f"anchors/{merkle_root[:16]}.ots"
    with open(proof_path, 'wb') as f:
        f.write(timestamp.serialize())
    
    return {
        "anchor_type": "OPENTIMESTAMPS",
        "target": "BITCOIN",
        "merkle_root": merkle_root,
        "proof_file": proof_path,
        "status": "PENDING"  # Confirmed in ~2 hours
    }

def verify_opentimestamps(merkle_root: str, proof_path: str) -> bool:
    """Verify anchor proof."""
    with open(proof_path, 'rb') as f:
        timestamp = opentimestamps.Timestamp.deserialize(f.read())
    
    return opentimestamps.verify(timestamp, bytes.fromhex(merkle_root))
```

### 5.3 RFC 3161 TSA (Gold/Platinum)

```python
import requests
from cryptography.x509 import tsp

def anchor_rfc3161(merkle_root: str, tsa_url: str) -> dict:
    """
    Anchor to RFC 3161 Time Stamp Authority.
    
    TSA URLs:
    - FreeTSA: https://freetsa.org/tsr
    - DigiCert: https://timestamp.digicert.com
    """
    request = tsp.TimeStampRequest(
        message_imprint=tsp.MessageImprint(
            hash_algorithm=hashes.SHA256(),
            hashed_message=bytes.fromhex(merkle_root)
        ),
        cert_req=True
    )
    
    response = requests.post(
        tsa_url,
        data=request.public_bytes(),
        headers={"Content-Type": "application/timestamp-query"}
    )
    
    tsr = tsp.TimeStampResponse.from_bytes(response.content)
    
    return {
        "anchor_type": "RFC3161",
        "tsa_url": tsa_url,
        "merkle_root": merkle_root,
        "serial_number": str(tsr.serial_number),
        "tsr_bytes": response.content.hex()
    }
```

### 5.4 Anchor Unavailability Handling

```python
class AnchorManager:
    def __init__(self, primary, fallbacks: list):
        self.primary = primary
        self.fallbacks = fallbacks
        self.pending = []
    
    def anchor(self, merkle_root: str) -> dict:
        try:
            return self.primary.anchor(merkle_root)
        except Exception:
            for fallback in self.fallbacks:
                try:
                    return fallback.anchor(merkle_root)
                except:
                    continue
            
            # Queue for retry
            self.pending.append({
                "merkle_root": merkle_root,
                "queued_at": datetime.now(timezone.utc)
            })
            raise Exception("All anchor targets unavailable")
```

---

## 6. Policy Identification

### 6.1 Schema

**REQUIRED in v1.1.**

```json
{
  "policy_identification": {
    "version": "1.1",
    "policy_id": "com.example:silver-mt5-v1",
    "conformance_tier": "SILVER",
    "verification_depth": {
      "hash_chain_validation": false,
      "merkle_proof_required": true,
      "external_anchor_required": true
    }
  }
}
```

### 6.2 PolicyID Naming Convention

```
PolicyID = <reverse-domain>:<local-identifier>

Examples:
  org.veritaschain.prod:hft-system-001
  com.propfirm.eval:silver-challenge-v2
  jp.co.fintokei:gold-algo-v1
```

### 6.3 Implementation

```python
from dataclasses import dataclass

@dataclass
class PolicyIdentification:
    version: str = "1.1"
    policy_id: str = ""
    conformance_tier: str = "SILVER"
    hash_chain_validation: bool = False
    merkle_proof_required: bool = True
    external_anchor_required: bool = True
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "policy_id": self.policy_id,
            "conformance_tier": self.conformance_tier,
            "verification_depth": {
                "hash_chain_validation": self.hash_chain_validation,
                "merkle_proof_required": self.merkle_proof_required,
                "external_anchor_required": self.external_anchor_required
            }
        }
```

---

## 7. Error Event Standardization

### 7.1 Standard Error Types (NEW in v1.1)

| EventType | Category | Severity |
|-----------|----------|----------|
| ERR_CONN | Connection | CRITICAL |
| ERR_AUTH | Authentication | CRITICAL |
| ERR_TIMEOUT | Timeout | WARNING |
| ERR_REJECT | Order Rejection | WARNING |
| ERR_PARSE | Parse Error | WARNING |
| ERR_SYNC | Clock Sync Lost | WARNING |
| ERR_RISK | Risk Limit Breach | CRITICAL |
| ERR_SYSTEM | System Error | CRITICAL |
| ERR_RECOVER | Recovery Started | INFO |

### 7.2 Error Event Schema

```json
{
  "header": {
    "event_type": "ERR_RISK",
    "vcp_version": "1.1"
  },
  "payload": {
    "error_details": {
      "error_code": "MAX_POSITION_EXCEEDED",
      "error_message": "Position 150 lots exceeds limit 100",
      "severity": "CRITICAL",
      "affected_component": "risk-manager",
      "recovery_action": "Order rejected",
      "correlated_event_id": "uuid-of-related-order"
    }
  }
}
```

### 7.3 Implementation

```python
def log_error(client, error_type: str, code: str, message: str, 
              severity: str, component: str, correlated_id: str = None):
    """
    Log standardized error event.
    
    IMPORTANT: Error events MUST be included in Merkle batches.
    """
    payload = {
        "error_details": {
            "error_code": code,
            "error_message": message,
            "severity": severity,
            "affected_component": component
        }
    }
    
    if correlated_id:
        payload["error_details"]["correlated_event_id"] = correlated_id
    
    return client.log(error_type, payload)

# Example
log_error(
    client=vcp,
    error_type="ERR_RISK",
    code="MAX_DRAWDOWN_EXCEEDED",
    message="Daily drawdown 12% exceeds limit 10%",
    severity="CRITICAL",
    component="risk-manager"
)
```

---

## 8. VCP-XREF Dual Logging

### 8.1 Overview

VCP-XREF enables **dual logging** - multiple parties record the same transaction for cross-verification.

```
┌──────────────────┐          ┌──────────────────┐
│     Trader       │─────────▶│     Broker       │
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│   VCP Sidecar    │          │   Broker VCP     │
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         └───────────┬─────────────────┘
                     ▼
            ┌─────────────────┐
            │  Cross-Reference │
            │   Verification   │
            └─────────────────┘
```

### 8.2 Schema

```json
{
  "vcp_xref": {
    "version": "1.1",
    "cross_reference_id": "uuid",
    "party_role": "INITIATOR",
    "counterparty_id": "broker.example.com",
    "shared_event_key": {
      "order_id": "ORD-12345",
      "timestamp": 1735560000000,
      "tolerance_ms": 1000
    },
    "reconciliation_status": "PENDING"
  }
}
```

### 8.3 Use Cases

| Scenario | Benefit |
|----------|---------|
| **Prop Firm Trading** | Prevent payout disputes |
| **Broker Execution** | Verify best execution |
| **Regulatory Audit** | Independent verification |

---

## 9. Complete Code Examples

### 9.1 Python (Silver Tier)

```python
"""
VCP v1.1 Silver Tier - Complete Example
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone

# --- Merkle Tree ---

class MerkleTree:
    """RFC 6962 tree over decoded 32-byte event hashes (v1.1 example)."""

    def __init__(self):
        self.leaves: list[bytes] = []

    def add(self, event_hash: str):
        """Hash the event-hash bytes as leaf data, exactly once."""
        if not isinstance(event_hash, str) or len(event_hash) != 64:
            raise ValueError("event_hash must be 64 hexadecimal characters")
        data = bytes.fromhex(event_hash)
        if len(data) != 32:
            raise ValueError("event_hash must encode exactly 32 bytes")
        self.leaves.append(hashlib.sha256(b'\x00' + data).digest())

    def _root(self, start: int, size: int) -> bytes:
        if size == 0:
            return hashlib.sha256(b'').digest()
        if size == 1:
            return self.leaves[start]
        # Largest power of two strictly smaller than size (RFC 6962 §2.1).
        k = 1 << ((size - 1).bit_length() - 1)
        return hashlib.sha256(
            b'\x01' + self._root(start, k) + self._root(start + k, size - k)
        ).digest()

    def root(self) -> str:
        return self._root(0, len(self.leaves)).hex()

    def proof(self, index: int) -> list[dict[str, str]]:
        """Bottom-up audit path; position describes the sibling's side."""
        if type(index) is not int or not 0 <= index < len(self.leaves):
            raise ValueError("leaf index out of range")

        def path(start: int, size: int, offset: int) -> list[dict[str, str]]:
            if size == 1:
                return []
            k = 1 << ((size - 1).bit_length() - 1)
            if offset < k:
                return path(start, k, offset) + [{
                    "hash": self._root(start + k, size - k).hex(),
                    "position": "right",
                }]
            return path(start + k, size - k, offset - k) + [{
                "hash": self._root(start, k).hex(),
                "position": "left",
            }]

        return path(0, len(self.leaves), index)

    def reset(self):
        self.leaves = []

# --- VCP Client ---

class VCPClient:
    def __init__(self, policy_id: str, tier: str = "SILVER"):
        self.policy_id = policy_id
        self.tier = tier
        self.tree = MerkleTree()
        self.events = []
    
    def log(self, event_type: str, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        
        event = {
            "header": {
                "event_id": str(uuid.uuid4()),
                "event_type": event_type,
                "timestamp_iso": now.isoformat(),
                "timestamp_int": str(int(now.timestamp() * 1000)),
                "timestamp_precision": "MILLISECOND",
                "clock_sync_status": "BEST_EFFORT",
                "vcp_version": "1.1",
                "hash_algo": "SHA256"
            },
            "payload": payload,
            "policy_identification": {
                "version": "1.1",
                "policy_id": self.policy_id,
                "conformance_tier": self.tier,
                "verification_depth": {
                    "hash_chain_validation": False,
                    "merkle_proof_required": True,
                    "external_anchor_required": True
                }
            }
        }
        
        # Compute hash
        hashable = {"header": event["header"], "payload": event["payload"]}
        canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'))
        event_hash = hashlib.sha256(canonical.encode()).hexdigest()
        
        event["security"] = {"event_hash": event_hash}
        
        self.tree.add(event_hash)
        self.events.append(event)
        
        return event
    
    def anchor(self) -> dict:
        """Anchor to external store - REQUIRED in v1.1."""
        root = self.tree.root()
        
        result = {
            "merkle_root": root,
            "event_count": len(self.events),
            "anchored_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.tree.reset()
        self.events = []
        
        return result

# --- Usage ---

if __name__ == "__main__":
    client = VCPClient("com.example:silver-v1")
    
    # Log order
    order = client.log("ORD", {
        "trade_data": {
            "order_id": "ORD-001",
            "symbol": "XAUUSD",
            "side": "BUY",
            "price": "2650.50",
            "quantity": "1.0"
        }
    })
    print(f"Order: {order['header']['event_id']}")
    
    # Log execution
    exe = client.log("EXE", {
        "trade_data": {
            "order_id": "ORD-001",
            "execution_price": "2650.45",
            "executed_qty": "1.0"
        }
    })
    print(f"Execution: {exe['header']['event_id']}")
    
    # Anchor
    anchor = client.anchor()
    print(f"Anchored: {anchor['merkle_root']}")
```

### 9.2 TypeScript

```typescript
import { createHash } from 'crypto';

interface VCPEvent {
  header: {
    event_id: string;
    event_type: string;
    timestamp_iso: string;
    timestamp_int: string;
    vcp_version: string;
  };
  payload: Record<string, unknown>;
  policy_identification: {
    version: string;
    policy_id: string;
    conformance_tier: string;
  };
  security: {
    event_hash: string;
  };
}

class MerkleTree {
  private leaves: Buffer[] = [];

  add(eventHash: string): void {
    if (typeof eventHash !== 'string' || eventHash.length !== 64 ||
        !/^[0-9a-fA-F]{64}$/.test(eventHash)) {
      throw new Error('eventHash must be 64 hexadecimal characters');
    }
    this.leaves.push(createHash('sha256')
      .update(Buffer.concat([Buffer.from([0x00]), Buffer.from(eventHash, 'hex')]))
      .digest());
  }

  private split(size: number): number {
    let k = 1;
    while (k * 2 < size) k *= 2;
    return k;
  }

  private subtreeRoot(start: number, size: number): Buffer {
    if (size === 0) return createHash('sha256').update(Buffer.alloc(0)).digest();
    if (size === 1) return this.leaves[start];
    const k = this.split(size);
    return createHash('sha256')
      .update(Buffer.concat([
        Buffer.from([0x01]),
        this.subtreeRoot(start, k),
        this.subtreeRoot(start + k, size - k),
      ]))
      .digest();
  }

  root(): string {
    return this.subtreeRoot(0, this.leaves.length).toString('hex');
  }

  proof(index: number): Array<{ hash: string; position: 'left' | 'right' }> {
    if (!Number.isInteger(index) || index < 0 || index >= this.leaves.length) {
      throw new Error('leaf index out of range');
    }
    const path = (start: number, size: number, offset: number):
      Array<{ hash: string; position: 'left' | 'right' }> => {
      if (size === 1) return [];
      const k = this.split(size);
      if (offset < k) {
        return [...path(start, k, offset), {
          hash: this.subtreeRoot(start + k, size - k).toString('hex'),
          position: 'right',
        }];
      }
      return [...path(start + k, size - k, offset - k), {
        hash: this.subtreeRoot(start, k).toString('hex'),
        position: 'left',
      }];
    };
    return path(0, this.leaves.length, index);
  }

  reset(): void {
    this.leaves = [];
  }
}

class VCPClient {
  private policyId: string;
  private tree: MerkleTree;

  constructor(policyId: string) {
    this.policyId = policyId;
    this.tree = new MerkleTree();
  }

  log(eventType: string, payload: Record<string, unknown>): VCPEvent {
    const now = new Date();
    
    const event: VCPEvent = {
      header: {
        event_id: crypto.randomUUID(),
        event_type: eventType,
        timestamp_iso: now.toISOString(),
        timestamp_int: now.getTime().toString(),
        vcp_version: '1.1',
      },
      payload,
      policy_identification: {
        version: '1.1',
        policy_id: this.policyId,
        conformance_tier: 'SILVER',
      },
      security: { event_hash: '' },
    };

    const hashContent = JSON.stringify({ header: event.header, payload: event.payload });
    event.security.event_hash = createHash('sha256').update(hashContent).digest('hex');
    
    this.tree.add(event.security.event_hash);
    return event;
  }

  anchor(): { merkleRoot: string; anchoredAt: string } {
    const root = this.tree.root();
    this.tree.reset();
    return { merkleRoot: root, anchoredAt: new Date().toISOString() };
  }
}
```

### 9.3 MQL5 Bridge

```mql5
//+------------------------------------------------------------------+
//| VCP v1.1 MQL5 Bridge                                              |
//+------------------------------------------------------------------+
#property copyright "VeritasChain Standards Organization"
#property version   "1.10"

#include <JAson.mqh>

input string VCP_PolicyID = "com.example:silver-mt5";
input string VCP_SidecarURL = "http://localhost:8080/vcp/log";

class CVCPLogger
{
private:
    string m_policyId;
    string m_sidecarUrl;
    
public:
    CVCPLogger(string policyId, string sidecarUrl)
    {
        m_policyId = policyId;
        m_sidecarUrl = sidecarUrl;
    }
    
    bool LogOrder(string orderId, string symbol, string side, double price, double qty)
    {
        CJAVal event;
        
        event["header"]["event_type"] = "ORD";
        event["header"]["timestamp_iso"] = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
        event["header"]["timestamp_int"] = IntegerToString(TimeCurrent() * 1000);
        event["header"]["vcp_version"] = "1.1";
        
        event["payload"]["trade_data"]["order_id"] = orderId;
        event["payload"]["trade_data"]["symbol"] = symbol;
        event["payload"]["trade_data"]["side"] = side;
        event["payload"]["trade_data"]["price"] = DoubleToString(price, 5);
        event["payload"]["trade_data"]["quantity"] = DoubleToString(qty, 2);
        
        // Policy Identification (REQUIRED in v1.1)
        event["policy_identification"]["version"] = "1.1";
        event["policy_identification"]["policy_id"] = m_policyId;
        event["policy_identification"]["conformance_tier"] = "SILVER";
        
        return SendToSidecar(event.Serialize());
    }
    
    bool LogExecution(string orderId, string symbol, double execPrice, double execQty)
    {
        CJAVal event;
        
        event["header"]["event_type"] = "EXE";
        event["header"]["timestamp_iso"] = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
        event["header"]["timestamp_int"] = IntegerToString(TimeCurrent() * 1000);
        event["header"]["vcp_version"] = "1.1";
        
        event["payload"]["trade_data"]["order_id"] = orderId;
        event["payload"]["trade_data"]["symbol"] = symbol;
        event["payload"]["trade_data"]["execution_price"] = DoubleToString(execPrice, 5);
        event["payload"]["trade_data"]["executed_qty"] = DoubleToString(execQty, 2);
        
        event["policy_identification"]["version"] = "1.1";
        event["policy_identification"]["policy_id"] = m_policyId;
        event["policy_identification"]["conformance_tier"] = "SILVER";
        
        return SendToSidecar(event.Serialize());
    }
    
private:
    bool SendToSidecar(string jsonData)
    {
        char data[], result[];
        string headers = "Content-Type: application/json\r\n";
        
        StringToCharArray(jsonData, data, 0, StringLen(jsonData));
        
        int res = WebRequest("POST", m_sidecarUrl, headers, 5000, data, result, headers);
        
        if(res == -1)
        {
            Print("VCP Sidecar error: ", GetLastError());
            return false;
        }
        
        return (res == 200 || res == 201);
    }
};

// Global instance
CVCPLogger* g_vcp = NULL;

int OnInit()
{
    g_vcp = new CVCPLogger(VCP_PolicyID, VCP_SidecarURL);
    return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
    if(g_vcp != NULL) delete g_vcp;
}

void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
{
    if(g_vcp == NULL) return;
    
    if(trans.type == TRADE_TRANSACTION_ORDER_ADD)
    {
        g_vcp.LogOrder(
            IntegerToString(trans.order),
            trans.symbol,
            (trans.order_type == ORDER_TYPE_BUY) ? "BUY" : "SELL",
            trans.price,
            trans.volume
        );
    }
    else if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
    {
        g_vcp.LogExecution(
            IntegerToString(trans.order),
            trans.symbol,
            trans.price,
            trans.volume
        );
    }
}
```

---

## 10. Migration from v1.0

### 10.1 Step-by-Step

**Step 1: Add Policy Identification (REQUIRED)**

```python
# Before (v1.0)
event = {
    "header": {...},
    "payload": {...},
    "security": {...}
}

# After (v1.1)
event = {
    "header": {...},
    "payload": {...},
    "policy_identification": {  # ADD THIS
        "version": "1.1",
        "policy_id": "com.yourcompany:system-001",
        "conformance_tier": "SILVER"
    },
    "security": {...}
}
```

**Step 2: Add External Anchoring (Silver Tier)**

```python
# Install OpenTimestamps
# pip install opentimestamps-client

def daily_anchor(merkle_root: str):
    import opentimestamps
    timestamp = opentimestamps.stamp(bytes.fromhex(merkle_root))
    
    with open(f"anchor_{date.today()}.ots", 'wb') as f:
        f.write(timestamp.serialize())
```

**Step 3: (Optional) Remove Hash Chain**

```python
# v1.1: prev_hash is OPTIONAL
security = {
    "event_hash": event_hash
    # prev_hash can be omitted
}
```

### 10.2 Checklist

```
[ ] Update vcp_version: "1.0" → "1.1"
[ ] Add policy_identification to all events
[ ] Implement external anchoring (Silver tier)
[ ] Update tests
[ ] Run conformance suite
```

---

## 11. Conformance Testing

### 11.1 v1.1 Test Matrix

| Test | Silver | Gold | Platinum |
|------|--------|------|----------|
| Schema Validation | ✓ | ✓ | ✓ |
| UUID v7 Format | ✓ | ✓ | ✓ |
| EventHash | ✓ | ✓ | ✓ |
| PrevHash | **OPTIONAL** | OPTIONAL | OPTIONAL |
| Merkle Tree | ✓ | ✓ | ✓ |
| External Anchor | ✓ | ✓ | ✓ |
| Policy Identification | ✓ | ✓ | ✓ |
| Digital Signature | ✓ | ✓ | ✓ |

### 11.2 Running Tests

**Local Merkle regression tests (v1.1 examples only):**

```bash
# Python 3.10+ and Node.js 22.18+; no Python/npm packages or network required
python -m unittest discover -s tests -v
```

These tests execute the Python tree examples in §§3.3 and 9.1, the TypeScript
tree in §9.2, and the README proof verifier directly from their code fences.
Frozen known values cover 0–8 leaves, including unbalanced 3-, 5-, 6-, and
7-leaf trees. Round trips, cross-language paths, tampering, malformed inputs,
and regressions to missing prefixes or duplicate-last trees are checked.
See [test/vector documentation](./tests/README.md). Passing these checks is
not a v1.1 certification or a VCP v1.2 conformance declaration.

**Broader conformance tooling (existing guidance):**

```bash
pip install vcp-conformance-test

# Silver tier
vcp-test --tier silver --version 1.1 ./implementation

# Generate report
vcp-test --tier silver --version 1.1 --report ./implementation
```

---

## 12. Sidecar Deployment

### 12.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EXISTING INFRASTRUCTURE                           │
│                      (NO MODIFICATIONS)                              │
├─────────────────────────────────────────────────────────────────────┤
│  [Trading Algo] [Risk Mgmt] [Order Mgmt] [Market Data]              │
│                         │                                            │
│                   [Event Stream]                                     │
│                         │                                            │
├─────────────────────────┼────────────────────────────────────────────┤
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                       VCP SIDECAR                            │    │
│  │  [Capture] → [Hash] → [Merkle] → [Anchor]                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                          VCP LAYER                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 Integration Patterns

| Pattern | Description | Best For |
|---------|-------------|----------|
| API Interception | Copy REST/FIX traffic | Gold/Platinum |
| In-Process Hook | DLL integration | Silver (MT4/MT5) |
| Message Queue Tap | Kafka/Redis subscribe | Institutional |

### 12.3 Design Principles

| Principle | Description |
|-----------|-------------|
| **Non-invasive** | No changes to trading logic |
| **Fail-safe** | VCP failure ≠ trading failure |
| **Async-first** | No latency impact |

---

## 13. Appendices

### Appendix A: JSON Schema v1.1

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://veritaschain.org/schemas/vcp-event-v1.1.json",
  "type": "object",
  "required": ["header", "payload", "policy_identification", "security"],
  "properties": {
    "header": {
      "type": "object",
      "required": ["event_id", "event_type", "timestamp_iso", "timestamp_int", "vcp_version"],
      "properties": {
        "event_id": { "type": "string", "format": "uuid" },
        "event_type": { "type": "string" },
        "timestamp_iso": { "type": "string", "format": "date-time" },
        "timestamp_int": { "type": "string", "pattern": "^[0-9]+$" },
        "vcp_version": { "type": "string", "const": "1.1" }
      }
    },
    "payload": { "type": "object" },
    "policy_identification": {
      "type": "object",
      "required": ["version", "policy_id", "conformance_tier"],
      "properties": {
        "version": { "type": "string", "const": "1.1" },
        "policy_id": { "type": "string" },
        "conformance_tier": { "type": "string", "enum": ["SILVER", "GOLD", "PLATINUM"] }
      }
    },
    "security": {
      "type": "object",
      "required": ["event_hash"],
      "properties": {
        "event_hash": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
        "prev_hash": { "type": "string", "pattern": "^[0-9a-f]{64}$" }
      }
    }
  }
}
```

### Appendix B: Implementation Checklist

**All Tiers:**
```
[ ] UUID v4/v7 event ID
[ ] Dual timestamp (ISO + int64)
[ ] EventHash (SHA-256)
[ ] Policy Identification
[ ] Merkle Tree (RFC 6962)
[ ] External Anchoring
[ ] JSON canonicalization
```

**Silver:**
```
[ ] MILLISECOND precision
[ ] BEST_EFFORT clock sync
[ ] Daily anchoring (OpenTimestamps)
```

**Gold:**
```
[ ] MICROSECOND precision
[ ] NTP_SYNCED clock sync
[ ] Hourly anchoring
[ ] Ed25519 self-signing
```

**Platinum:**
```
[ ] NANOSECOND precision
[ ] PTP_LOCKED clock sync
[ ] 10-minute anchoring
[ ] HSM key management
```

---

## Contact

**VeritasChain Standards Organization (VSO)**

- Website: https://veritaschain.org
- GitHub: https://github.com/veritaschain
- Technical: technical@veritaschain.org
- Standards: standards@veritaschain.org

---

*Copyright © 2025 VeritasChain Standards Organization. Apache 2.0 License.*
