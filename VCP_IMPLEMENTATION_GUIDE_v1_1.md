# VeritasChain Protocol Implementation Guide v1.1

**Document ID:** VSO-IMPL-001  
**Status:** Production Ready  
**Version:** 1.1.0  
**Date:** 2025-12-30  
**Maintainer:** VeritasChain Standards Organization (VSO)  
**License:** Apache 2.0

---

## Abstract

This document provides comprehensive implementation guidance for VeritasChain Protocol (VCP) v1.1. It covers the three-layer architecture, mandatory external anchoring, Policy Identification, VCP-XREF dual logging, error event standardization, and migration from v1.0.

The guide includes practical code examples in Python, TypeScript, and MQL5, along with deployment patterns and conformance testing requirements.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [What's New in v1.1](#2-whats-new-in-v11)
3. [Three-Layer Architecture](#3-three-layer-architecture)
4. [Implementation by Tier](#4-implementation-by-tier)
5. [External Anchoring Implementation](#5-external-anchoring-implementation)
6. [Policy Identification](#6-policy-identification)
7. [VCP-XREF Dual Logging](#7-vcp-xref-dual-logging)
8. [Error Event Handling](#8-error-event-handling)
9. [Code Examples](#9-code-examples)
10. [Migration from v1.0](#10-migration-from-v10)
11. [Conformance Testing](#11-conformance-testing)
12. [Deployment Patterns](#12-deployment-patterns)
13. [Appendices](#13-appendices)

---

## 1. Introduction

### 1.1 Purpose

This guide enables developers to implement VCP v1.1 compliant systems for:

- Algorithmic trading platforms
- Prop firm evaluation systems  
- Broker execution logging
- Risk management audit trails
- AI decision logging (EU AI Act compliance)

### 1.2 Audience

- Software engineers implementing VCP integration
- System architects designing audit infrastructure
- DevOps engineers deploying VCP sidecars
- QA engineers validating conformance

### 1.3 Prerequisites

- VCP Specification v1.1 (VSO-SPEC-001)
- Understanding of cryptographic hashing (SHA-256)
- Familiarity with Merkle trees (RFC 6962)
- Basic knowledge of digital signatures (Ed25519)

### 1.4 Conformance Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHOULD", "RECOMMENDED", "MAY", and "OPTIONAL" are interpreted as described in RFC 2119.

---

## 2. What's New in v1.1

### 2.1 Summary of Changes

| Change | v1.0 | v1.1 | Impact |
|--------|------|------|--------|
| External Anchoring | OPTIONAL (Silver) | **REQUIRED (All)** | Implementation required |
| PrevHash (Hash Chain) | REQUIRED | **OPTIONAL** | Simplification allowed |
| Policy Identification | N/A | **REQUIRED** | New field required |
| VCP-XREF | N/A | **OPTIONAL** | New extension available |
| Error Events | Ad-hoc | **Standardized** | Schema update |
| Three-Layer Architecture | Implicit | **Explicit** | Documentation only |

### 2.2 Breaking Changes

**Protocol Level:** None. v1.1 is fully backward compatible with v1.0.

**Certification Level:** The following changes affect VC-Certified status:

1. **External Anchoring**: Silver tier implementations MUST add daily anchoring
2. **Policy Identification**: All tiers MUST include PolicyID in events

### 2.3 Grace Period

| Requirement | Deadline |
|-------------|----------|
| External Anchoring (Silver) | 2026-06-25 |
| Policy Identification | 2026-03-25 |

---

## 3. Three-Layer Architecture

### 3.1 Overview

VCP v1.1 explicitly defines a three-layer architecture for integrity and security:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  LAYER 3: External Verifiability                                    │
│  ────────────────────────────                                       │
│  Purpose: Third-party verification without trusting the producer    │
│                                                                     │
│  Components:                                                        │
│  ├─ Digital Signature (Ed25519/Dilithium): REQUIRED                │
│  ├─ Timestamp (Dual ISO+int64): REQUIRED                           │
│  └─ External Anchor: REQUIRED (Tier-dependent frequency)           │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYER 2: Collection Integrity                                      │
│  ─────────────────────────────                                      │
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
│  ────────────────────────                                           │
│  Purpose: Individual event integrity                                │
│                                                                     │
│  Components:                                                        │
│  ├─ EventHash (SHA-256 of canonicalized event): REQUIRED           │
│  └─ PrevHash (Link to previous event): OPTIONAL                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Layer 1: Event Integrity

Each event MUST have an `event_hash` computed as:

```python
import hashlib
import json

def compute_event_hash(event: dict) -> str:
    """
    Compute EventHash per VCP v1.1 specification.
    
    1. Extract hashable content (header + payload, excluding security)
    2. Canonicalize using RFC 8785 (JCS)
    3. Apply SHA-256
    """
    # Step 1: Extract hashable content
    hashable = {
        "header": event["header"],
        "payload": event["payload"]
    }
    
    # Step 2: Canonicalize (RFC 8785)
    # Note: Use a proper JCS library in production
    canonical = canonicalize_json(hashable)
    
    # Step 3: SHA-256
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

**PrevHash (OPTIONAL in v1.1):**

```python
def compute_prev_hash(previous_event: dict) -> str:
    """
    Compute PrevHash linking to previous event.
    OPTIONAL in v1.1, but RECOMMENDED for:
    - MiFID II RTS 25 compliance
    - Real-time tampering detection
    """
    return previous_event["security"]["event_hash"]
```

### 3.3 Layer 2: Collection Integrity

Events are batched into Merkle trees per RFC 6962:

```python
import hashlib
from typing import List

class MerkleTree:
    """RFC 6962 compliant Merkle Tree implementation."""
    
    def __init__(self):
        self.leaves: List[bytes] = []
    
    def add_event(self, event_hash: str):
        """Add event hash as leaf."""
        # Leaf hash: H(0x00 || event_hash)
        leaf = hashlib.sha256(
            b'\x00' + bytes.fromhex(event_hash)
        ).digest()
        self.leaves.append(leaf)
    
    def compute_root(self) -> str:
        """Compute Merkle root."""
        if not self.leaves:
            return "0" * 64
        
        nodes = self.leaves.copy()
        while len(nodes) > 1:
            if len(nodes) % 2 == 1:
                nodes.append(nodes[-1])  # Duplicate last if odd
            
            next_level = []
            for i in range(0, len(nodes), 2):
                # Internal node: H(0x01 || left || right)
                combined = hashlib.sha256(
                    b'\x01' + nodes[i] + nodes[i+1]
                ).digest()
                next_level.append(combined)
            nodes = next_level
        
        return nodes[0].hex()
    
    def get_audit_path(self, index: int) -> List[str]:
        """Generate audit path for event at index."""
        # Implementation per RFC 6962
        path = []
        # ... (full implementation in Appendix A)
        return path
```

### 3.4 Layer 3: External Verifiability

**REQUIRED for all tiers in v1.1.**

The Merkle root MUST be anchored to an external, tamper-evident store:

| Tier | Frequency | Anchor Targets |
|------|-----------|----------------|
| Platinum | Every 10 minutes | Blockchain, RFC 3161 TSA |
| Gold | Every 1 hour | RFC 3161 TSA, Certified Database |
| Silver | Every 24 hours | OpenTimestamps, FreeTSA, Certified Database |

---

## 4. Implementation by Tier

### 4.1 Silver Tier (Retail/MT4/MT5)

**Minimum Requirements:**

```yaml
Clock Sync: BEST_EFFORT (system clock)
Timestamp Precision: MILLISECOND
Serialization: JSON
Signature: Delegated (VCC signs) OR Client Ed25519
External Anchor: REQUIRED - Daily (every 24 hours)
Hash Chain (PrevHash): OPTIONAL
```

**Silver Tier Implementation Skeleton:**

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import uuid

@dataclass
class SilverTierConfig:
    policy_id: str              # REQUIRED in v1.1
    conformance_tier: str = "SILVER"
    anchor_interval_hours: int = 24
    use_hash_chain: bool = False  # OPTIONAL in v1.1

class VCPSilverClient:
    def __init__(self, config: SilverTierConfig):
        self.config = config
        self.merkle_tree = MerkleTree()
        self.last_anchor_time: Optional[datetime] = None
        self.event_count = 0
    
    def log_event(self, event_type: str, payload: dict) -> dict:
        """Log a VCP event (Silver tier)."""
        
        # Generate header
        header = {
            "event_id": str(uuid.uuid7()),
            "event_type": event_type,
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "timestamp_int": str(int(datetime.now(timezone.utc).timestamp() * 1000)),
            "timestamp_precision": "MILLISECOND",
            "clock_sync_status": "BEST_EFFORT",
            "vcp_version": "1.1",
            "sign_algo": "ED25519",
            "hash_algo": "SHA256"
        }
        
        # Build event
        event = {
            "header": header,
            "payload": payload,
            "policy_identification": {  # NEW in v1.1
                "version": "1.1",
                "policy_id": self.config.policy_id,
                "conformance_tier": self.config.conformance_tier
            }
        }
        
        # Compute EventHash
        event_hash = compute_event_hash(event)
        
        # Security section
        event["security"] = {
            "event_hash": event_hash
        }
        
        # Add to Merkle tree
        self.merkle_tree.add_event(event_hash)
        self.event_count += 1
        
        # Check if anchoring needed
        self._check_anchor()
        
        return event
    
    def _check_anchor(self):
        """Check if daily anchor is due."""
        now = datetime.now(timezone.utc)
        
        if self.last_anchor_time is None:
            should_anchor = True
        else:
            hours_since = (now - self.last_anchor_time).total_seconds() / 3600
            should_anchor = hours_since >= self.config.anchor_interval_hours
        
        if should_anchor:
            self._perform_anchor()
    
    def _perform_anchor(self):
        """Anchor Merkle root to external store."""
        root = self.merkle_tree.compute_root()
        
        # Use OpenTimestamps (free, Bitcoin-backed)
        anchor_record = self._anchor_to_opentimestamps(root)
        
        self.last_anchor_time = datetime.now(timezone.utc)
        
        # Reset tree for next batch
        self.merkle_tree = MerkleTree()
        
        return anchor_record
    
    def _anchor_to_opentimestamps(self, merkle_root: str) -> dict:
        """Anchor to OpenTimestamps (Bitcoin)."""
        # Production: use opentimestamps-client library
        # This is a simplified example
        import opentimestamps
        
        timestamp = opentimestamps.stamp(bytes.fromhex(merkle_root))
        
        return {
            "anchor_type": "OPENTIMESTAMPS",
            "merkle_root": merkle_root,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "proof": timestamp.serialize().hex()
        }
```

### 4.2 Gold Tier (Prop Firms/Institutional)

**Requirements:**

```yaml
Clock Sync: NTP_SYNCED (<1ms accuracy)
Timestamp Precision: MICROSECOND
Serialization: JSON
Signature: Client Ed25519 (self-signing)
External Anchor: REQUIRED - Hourly
Hash Chain (PrevHash): RECOMMENDED
```

**Gold Tier Additions:**

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

class VCPGoldClient(VCPSilverClient):
    def __init__(self, config: GoldTierConfig, private_key: Ed25519PrivateKey):
        super().__init__(config)
        self.private_key = private_key
        self.config.anchor_interval_hours = 1
        self.config.use_hash_chain = True  # RECOMMENDED for Gold
        self.prev_hash: Optional[str] = None
    
    def log_event(self, event_type: str, payload: dict) -> dict:
        """Log a VCP event with self-signing (Gold tier)."""
        
        header = {
            "event_id": str(uuid.uuid7()),
            "event_type": event_type,
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "timestamp_int": str(int(datetime.now(timezone.utc).timestamp() * 1_000_000)),
            "timestamp_precision": "MICROSECOND",
            "clock_sync_status": "NTP_SYNCED",
            "vcp_version": "1.1",
            "sign_algo": "ED25519",
            "hash_algo": "SHA256"
        }
        
        event = {
            "header": header,
            "payload": payload,
            "policy_identification": {
                "version": "1.1",
                "policy_id": self.config.policy_id,
                "conformance_tier": "GOLD"
            }
        }
        
        event_hash = compute_event_hash(event)
        
        # Security with signature and optional hash chain
        security = {
            "event_hash": event_hash,
            "signature": self._sign(event_hash),
            "sign_algo": "ED25519"
        }
        
        # Hash chain (RECOMMENDED for Gold)
        if self.prev_hash:
            security["prev_hash"] = self.prev_hash
        
        event["security"] = security
        
        # Update chain
        self.prev_hash = event_hash
        self.merkle_tree.add_event(event_hash)
        
        self._check_anchor()
        
        return event
    
    def _sign(self, data: str) -> str:
        """Sign data with Ed25519."""
        signature = self.private_key.sign(bytes.fromhex(data))
        return signature.hex()
```

### 4.3 Platinum Tier (HFT/Exchanges)

**Requirements:**

```yaml
Clock Sync: PTP_LOCKED (<1µs accuracy)
Timestamp Precision: NANOSECOND
Serialization: SBE (Simple Binary Encoding) or JSON
Signature: Hardware Security Module (HSM) recommended
External Anchor: REQUIRED - Every 10 minutes
Hash Chain (PrevHash): RECOMMENDED
Performance: >1M events/sec, <10µs latency
```

**Platinum Tier Considerations:**

```python
# Platinum tier typically requires:
# 1. SBE binary encoding for performance
# 2. HSM integration for key management
# 3. PTP hardware timestamping
# 4. Kernel bypass networking (DPDK, etc.)

# This is beyond a simple code example.
# See: VSO-IMPL-PLATINUM-001 for detailed guidance.
```

---

## 5. External Anchoring Implementation

### 5.1 Anchor Targets by Tier

| Tier | Recommended | Alternative | Frequency |
|------|-------------|-------------|-----------|
| Silver | OpenTimestamps | FreeTSA, Certified DB | 24h |
| Gold | RFC 3161 TSA | Certified DB, Blockchain | 1h |
| Platinum | Ethereum/Bitcoin | RFC 3161 TSA | 10min |

### 5.2 OpenTimestamps (Silver Tier)

```python
# Installation: pip install opentimestamps-client

import opentimestamps
from opentimestamps.core.timestamp import Timestamp
from opentimestamps.core.op import OpSHA256

def anchor_opentimestamps(merkle_root: str) -> dict:
    """
    Anchor Merkle root to Bitcoin via OpenTimestamps.
    FREE service backed by Bitcoin blockchain.
    """
    root_bytes = bytes.fromhex(merkle_root)
    
    # Create timestamp
    file_timestamp = Timestamp(root_bytes)
    
    # Submit to OpenTimestamps calendars
    opentimestamps.stamp(file_timestamp)
    
    # Serialize proof (save this!)
    proof_bytes = file_timestamp.serialize()
    
    return {
        "anchor_type": "OPENTIMESTAMPS",
        "target": "BITCOIN",
        "merkle_root": merkle_root,
        "anchored_at": datetime.now(timezone.utc).isoformat(),
        "proof": proof_bytes.hex(),
        "status": "PENDING"  # Confirmed after ~2 hours
    }

def verify_opentimestamps(merkle_root: str, proof_hex: str) -> bool:
    """Verify OpenTimestamps proof."""
    proof_bytes = bytes.fromhex(proof_hex)
    timestamp = Timestamp.deserialize(proof_bytes)
    
    # Verify against Bitcoin
    return opentimestamps.verify(timestamp, bytes.fromhex(merkle_root))
```

### 5.3 RFC 3161 TSA (Gold/Platinum Tier)

```python
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.x509 import tsp

def anchor_rfc3161(merkle_root: str, tsa_url: str) -> dict:
    """
    Anchor Merkle root to RFC 3161 Time Stamp Authority.
    
    Popular TSAs:
    - FreeTSA: https://freetsa.org/tsr
    - DigiCert: https://timestamp.digicert.com
    - Sectigo: http://timestamp.sectigo.com
    """
    root_bytes = bytes.fromhex(merkle_root)
    
    # Create timestamp request
    request = tsp.TimeStampRequest(
        message_imprint=tsp.MessageImprint(
            hash_algorithm=hashes.SHA256(),
            hashed_message=root_bytes
        ),
        cert_req=True
    )
    
    # Send to TSA
    response = requests.post(
        tsa_url,
        data=request.public_bytes(),
        headers={"Content-Type": "application/timestamp-query"}
    )
    
    if response.status_code != 200:
        raise Exception(f"TSA request failed: {response.status_code}")
    
    # Parse response
    tsr = tsp.TimeStampResponse.from_bytes(response.content)
    
    return {
        "anchor_type": "RFC3161",
        "tsa_url": tsa_url,
        "merkle_root": merkle_root,
        "anchored_at": tsr.time_stamp_token.time.isoformat(),
        "serial_number": str(tsr.serial_number),
        "tsr_bytes": response.content.hex()
    }
```

### 5.4 Certified Database (All Tiers)

A "Certified Database" must meet these criteria:

1. **Third-Party Audit**: Annual independent audit (SOC 2 Type II or equivalent)
2. **Tamper Detection**: Cryptographic integrity checks
3. **Access Control**: Role-based access with audit logging
4. **Retention Policy**: Data retention ≥ regulatory minimum (typically 7 years)
5. **Availability SLA**: ≥ 99.9% uptime commitment

**Examples:**

- AWS QLDB (Quantum Ledger Database)
- Azure SQL Ledger
- Google Cloud Spanner with audit trail
- Self-hosted PostgreSQL with annual cryptographic audit

```python
def anchor_certified_db(merkle_root: str, db_client) -> dict:
    """
    Anchor to certified database with immutability guarantees.
    """
    record = {
        "merkle_root": merkle_root,
        "anchored_at": datetime.now(timezone.utc).isoformat(),
        "batch_id": str(uuid.uuid4())
    }
    
    # Insert with cryptographic verification
    result = db_client.insert_with_proof("vcp_anchors", record)
    
    return {
        "anchor_type": "CERTIFIED_DB",
        "database": db_client.name,
        "merkle_root": merkle_root,
        "anchored_at": record["anchored_at"],
        "record_id": result["id"],
        "db_proof": result["proof"]
    }
```

### 5.5 Anchor Target Unavailability

Implementations MUST handle anchor target unavailability:

```python
class AnchorManager:
    def __init__(self, primary_anchor, fallback_anchors: list):
        self.primary = primary_anchor
        self.fallbacks = fallback_anchors
        self.pending_anchors = []
    
    def anchor(self, merkle_root: str) -> dict:
        """Anchor with fallback support."""
        try:
            return self.primary.anchor(merkle_root)
        except Exception as e:
            # Try fallbacks
            for fallback in self.fallbacks:
                try:
                    return fallback.anchor(merkle_root)
                except:
                    continue
            
            # All failed - queue for retry
            self.pending_anchors.append({
                "merkle_root": merkle_root,
                "queued_at": datetime.now(timezone.utc),
                "retry_count": 0
            })
            
            raise Exception("All anchor targets unavailable")
    
    def retry_pending(self):
        """Retry pending anchors (call periodically)."""
        for pending in self.pending_anchors[:]:
            if pending["retry_count"] > 5:
                # Log critical error
                continue
            
            try:
                result = self.anchor(pending["merkle_root"])
                self.pending_anchors.remove(pending)
            except:
                pending["retry_count"] += 1
```

---

## 6. Policy Identification

### 6.1 Overview

Policy Identification is **REQUIRED** in v1.1. It declares which compliance tier and policy an event follows.

### 6.2 Schema

```json
{
  "PolicyIdentification": {
    "Version": "1.1",
    "PolicyID": "string",
    "ConformanceTier": "SILVER | GOLD | PLATINUM",
    "RegistrationPolicy": {
      "Issuer": "string",
      "PolicyURI": "string",
      "EffectiveDate": "int64",
      "ExpirationDate": "int64"
    },
    "VerificationDepth": {
      "HashChainValidation": "boolean",
      "MerkleProofRequired": "boolean",
      "ExternalAnchorRequired": "boolean"
    }
  }
}
```

### 6.3 PolicyID Naming Convention

```
PolicyID = <reverse-domain>:<local-identifier>

Examples:
  org.veritaschain.prod:hft-system-001
  com.propfirm.evaluation:silver-challenge-v2
  jp.co.broker:gold-algo-trading
```

### 6.4 Implementation

```python
@dataclass
class PolicyIdentification:
    version: str = "1.1"
    policy_id: str = ""
    conformance_tier: str = "SILVER"
    issuer: str = ""
    policy_uri: str = ""
    effective_date: Optional[int] = None
    expiration_date: Optional[int] = None
    hash_chain_validation: bool = False
    merkle_proof_required: bool = True
    external_anchor_required: bool = True  # Always True in v1.1
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "policy_id": self.policy_id,
            "conformance_tier": self.conformance_tier,
            "registration_policy": {
                "issuer": self.issuer,
                "policy_uri": self.policy_uri,
                "effective_date": self.effective_date,
                "expiration_date": self.expiration_date
            },
            "verification_depth": {
                "hash_chain_validation": self.hash_chain_validation,
                "merkle_proof_required": self.merkle_proof_required,
                "external_anchor_required": self.external_anchor_required
            }
        }

# Usage
policy = PolicyIdentification(
    policy_id="com.example:trading-algo-v1",
    conformance_tier="GOLD",
    issuer="Example Trading Corp",
    policy_uri="https://example.com/vcp-policy/gold-v1",
    hash_chain_validation=True
)
```

---

## 7. VCP-XREF Dual Logging

### 7.1 Overview

VCP-XREF enables **dual logging** where multiple independent parties record the same transaction. This provides higher assurance than single-party logging.

```
┌──────────────────┐          ┌──────────────────┐
│     Trader       │─────────▶│     Broker       │
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│   VCP Sidecar    │          │   Broker VCP     │
│   (Trader side)  │          │   (Broker side)  │
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         └───────────┬─────────────────┘
                     ▼
            ┌─────────────────┐
            │  Cross-Reference │
            │   Verification   │
            └─────────────────┘
```

### 7.2 Schema

```json
{
  "VCP-XREF": {
    "Version": "1.1",
    "CrossReferenceID": "uuid",
    "PartyRole": "INITIATOR | COUNTERPARTY | OBSERVER",
    "CounterpartyID": "string",
    "SharedEventKey": {
      "OrderID": "string",
      "AlternateKeys": ["string"],
      "Timestamp": "int64",
      "ToleranceMs": "int32"
    },
    "ReconciliationStatus": "PENDING | MATCHED | DISCREPANCY | TIMEOUT"
  }
}
```

### 7.3 Implementation

```python
import uuid
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class PartyRole(Enum):
    INITIATOR = "INITIATOR"
    COUNTERPARTY = "COUNTERPARTY"
    OBSERVER = "OBSERVER"

class ReconciliationStatus(Enum):
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    DISCREPANCY = "DISCREPANCY"
    TIMEOUT = "TIMEOUT"

@dataclass
class VCPXRef:
    cross_reference_id: str
    party_role: PartyRole
    counterparty_id: str
    order_id: str
    alternate_keys: List[str] = None
    timestamp: int = 0
    tolerance_ms: int = 1000
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.PENDING
    
    def to_dict(self) -> dict:
        return {
            "version": "1.1",
            "cross_reference_id": self.cross_reference_id,
            "party_role": self.party_role.value,
            "counterparty_id": self.counterparty_id,
            "shared_event_key": {
                "order_id": self.order_id,
                "alternate_keys": self.alternate_keys or [],
                "timestamp": self.timestamp,
                "tolerance_ms": self.tolerance_ms
            },
            "reconciliation_status": self.reconciliation_status.value
        }

# Trader side (INITIATOR)
trader_xref = VCPXRef(
    cross_reference_id=str(uuid.uuid4()),
    party_role=PartyRole.INITIATOR,
    counterparty_id="broker.example.com",
    order_id="ORD-12345",
    timestamp=int(datetime.now(timezone.utc).timestamp() * 1000)
)

# Broker side (COUNTERPARTY) - references same ID
broker_xref = VCPXRef(
    cross_reference_id=trader_xref.cross_reference_id,  # Same ID!
    party_role=PartyRole.COUNTERPARTY,
    counterparty_id="trader.example.com",
    order_id="ORD-12345",
    timestamp=int(datetime.now(timezone.utc).timestamp() * 1000)
)
```

### 7.4 Reconciliation

```python
class XRefReconciler:
    def __init__(self, db_client):
        self.db = db_client
    
    def reconcile(self, xref_id: str) -> ReconciliationStatus:
        """Reconcile events from both parties."""
        
        # Fetch events with this xref_id
        events = self.db.query(
            "SELECT * FROM vcp_events WHERE xref_id = ?",
            [xref_id]
        )
        
        if len(events) < 2:
            return ReconciliationStatus.PENDING
        
        initiator = next(e for e in events if e["party_role"] == "INITIATOR")
        counterparty = next(e for e in events if e["party_role"] == "COUNTERPARTY")
        
        # Compare key fields
        if self._compare_events(initiator, counterparty):
            return ReconciliationStatus.MATCHED
        else:
            return ReconciliationStatus.DISCREPANCY
    
    def _compare_events(self, e1: dict, e2: dict) -> bool:
        """Compare key fields within tolerance."""
        # Order ID must match exactly
        if e1["order_id"] != e2["order_id"]:
            return False
        
        # Timestamp within tolerance
        t1 = e1["timestamp"]
        t2 = e2["timestamp"]
        tolerance = max(e1["tolerance_ms"], e2["tolerance_ms"])
        
        if abs(t1 - t2) > tolerance:
            return False
        
        # Add more field comparisons as needed
        return True
```

---

## 8. Error Event Handling

### 8.1 Standardized Error Types (NEW in v1.1)

| EventType | Category | Severity | Description |
|-----------|----------|----------|-------------|
| ERR_CONN | Connection | CRITICAL | Connection failure |
| ERR_AUTH | Authentication | CRITICAL | Auth/authz failure |
| ERR_TIMEOUT | Timeout | WARNING | Operation timeout |
| ERR_REJECT | Rejection | WARNING | Order rejected |
| ERR_PARSE | Data | WARNING | Parse/validation failure |
| ERR_SYNC | Synchronization | WARNING | Clock sync lost |
| ERR_RISK | Risk | CRITICAL | Risk limit breach |
| ERR_SYSTEM | System | CRITICAL | Internal system error |
| ERR_RECOVER | Recovery | INFO | Recovery initiated |

### 8.2 Error Event Schema

```json
{
  "header": {
    "event_type": "ERR_CONN",
    "timestamp_iso": "2025-12-30T12:00:00.000Z",
    "timestamp_int": "1735560000000"
  },
  "error_details": {
    "error_code": "string",
    "error_message": "string",
    "severity": "CRITICAL | WARNING | INFO",
    "affected_component": "string",
    "recovery_action": "string",
    "correlated_event_id": "uuid"
  }
}
```

### 8.3 Implementation

```python
from enum import Enum

class ErrorSeverity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

class ErrorEventType(Enum):
    ERR_CONN = "ERR_CONN"
    ERR_AUTH = "ERR_AUTH"
    ERR_TIMEOUT = "ERR_TIMEOUT"
    ERR_REJECT = "ERR_REJECT"
    ERR_PARSE = "ERR_PARSE"
    ERR_SYNC = "ERR_SYNC"
    ERR_RISK = "ERR_RISK"
    ERR_SYSTEM = "ERR_SYSTEM"
    ERR_RECOVER = "ERR_RECOVER"

def log_error_event(
    client: VCPSilverClient,
    error_type: ErrorEventType,
    error_code: str,
    error_message: str,
    severity: ErrorSeverity,
    affected_component: str,
    recovery_action: str = None,
    correlated_event_id: str = None
) -> dict:
    """
    Log standardized error event.
    
    IMPORTANT: Error events MUST be included in Merkle batches
    and anchored. They MUST NOT be filtered out.
    """
    payload = {
        "error_details": {
            "error_code": error_code,
            "error_message": error_message,
            "severity": severity.value,
            "affected_component": affected_component
        }
    }
    
    if recovery_action:
        payload["error_details"]["recovery_action"] = recovery_action
    
    if correlated_event_id:
        payload["error_details"]["correlated_event_id"] = correlated_event_id
    
    return client.log_event(error_type.value, payload)

# Example: Connection error
log_error_event(
    client=vcp_client,
    error_type=ErrorEventType.ERR_CONN,
    error_code="BROKER_DISCONNECT",
    error_message="Lost connection to broker gateway",
    severity=ErrorSeverity.CRITICAL,
    affected_component="broker-gateway",
    recovery_action="Attempting reconnect with exponential backoff"
)

# Example: Risk limit breach
log_error_event(
    client=vcp_client,
    error_type=ErrorEventType.ERR_RISK,
    error_code="MAX_POSITION_EXCEEDED",
    error_message="Position size 150 lots exceeds limit of 100 lots",
    severity=ErrorSeverity.CRITICAL,
    affected_component="risk-manager",
    correlated_event_id="01934e3a-7b2c-7f93-8f2a-1234567890ab"
)
```

---

## 9. Code Examples

### 9.1 Complete Silver Tier Example (Python)

```python
"""
VCP v1.1 Silver Tier - Complete Implementation Example
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# --- Configuration ---

@dataclass
class VCPConfig:
    policy_id: str
    conformance_tier: str = "SILVER"
    anchor_interval_hours: int = 24
    use_hash_chain: bool = False

# --- Merkle Tree (RFC 6962) ---

class MerkleTree:
    def __init__(self):
        self.leaves: List[bytes] = []
    
    def add(self, event_hash: str):
        leaf = hashlib.sha256(b'\x00' + bytes.fromhex(event_hash)).digest()
        self.leaves.append(leaf)
    
    @property
    def root(self) -> str:
        if not self.leaves:
            return "0" * 64
        
        nodes = self.leaves.copy()
        while len(nodes) > 1:
            if len(nodes) % 2:
                nodes.append(nodes[-1])
            nodes = [
                hashlib.sha256(b'\x01' + nodes[i] + nodes[i+1]).digest()
                for i in range(0, len(nodes), 2)
            ]
        return nodes[0].hex()

# --- JSON Canonicalization (RFC 8785 simplified) ---

def canonicalize(obj: Any) -> str:
    """Simplified RFC 8785 canonicalization."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

# --- VCP Client ---

class VCPClient:
    def __init__(self, config: VCPConfig):
        self.config = config
        self.tree = MerkleTree()
        self.events: List[dict] = []
        self.last_anchor: Optional[datetime] = None
        self.prev_hash: Optional[str] = None
    
    def log(self, event_type: str, payload: dict) -> dict:
        """Log a VCP event."""
        now = datetime.now(timezone.utc)
        
        event = {
            "header": {
                "event_id": str(uuid.uuid7()) if hasattr(uuid, 'uuid7') else str(uuid.uuid4()),
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
                "policy_id": self.config.policy_id,
                "conformance_tier": self.config.conformance_tier,
                "verification_depth": {
                    "hash_chain_validation": self.config.use_hash_chain,
                    "merkle_proof_required": True,
                    "external_anchor_required": True
                }
            }
        }
        
        # Compute hash
        event_hash = hashlib.sha256(
            canonicalize({"header": event["header"], "payload": event["payload"]}).encode()
        ).hexdigest()
        
        security = {"event_hash": event_hash}
        
        if self.config.use_hash_chain and self.prev_hash:
            security["prev_hash"] = self.prev_hash
        
        event["security"] = security
        
        self.tree.add(event_hash)
        self.events.append(event)
        self.prev_hash = event_hash
        
        self._check_anchor()
        
        return event
    
    def _check_anchor(self):
        if self.last_anchor is None:
            return
        
        hours = (datetime.now(timezone.utc) - self.last_anchor).total_seconds() / 3600
        if hours >= self.config.anchor_interval_hours:
            self.anchor()
    
    def anchor(self) -> dict:
        """Anchor current batch to external store."""
        root = self.tree.root
        
        # In production: use OpenTimestamps, RFC 3161, etc.
        anchor_record = {
            "merkle_root": root,
            "event_count": len(self.events),
            "anchored_at": datetime.now(timezone.utc).isoformat(),
            "anchor_type": "OPENTIMESTAMPS"
        }
        
        # Reset for next batch
        self.tree = MerkleTree()
        self.events = []
        self.last_anchor = datetime.now(timezone.utc)
        
        return anchor_record

# --- Usage Example ---

if __name__ == "__main__":
    # Initialize
    config = VCPConfig(
        policy_id="com.example:silver-trading-v1",
        conformance_tier="SILVER"
    )
    client = VCPClient(config)
    
    # Log order
    order_event = client.log("ORD", {
        "trade_data": {
            "order_id": "ORD-001",
            "symbol": "XAUUSD",
            "side": "BUY",
            "order_type": "LIMIT",
            "price": "2650.50",
            "quantity": "1.0"
        }
    })
    print(f"Order logged: {order_event['header']['event_id']}")
    
    # Log execution
    exec_event = client.log("EXE", {
        "trade_data": {
            "order_id": "ORD-001",
            "symbol": "XAUUSD",
            "side": "BUY",
            "execution_price": "2650.45",
            "executed_qty": "1.0"
        }
    })
    print(f"Execution logged: {exec_event['header']['event_id']}")
    
    # Anchor
    anchor = client.anchor()
    print(f"Anchored: {anchor['merkle_root']}")
```

### 9.2 TypeScript Example

```typescript
// vcp-client.ts - VCP v1.1 TypeScript Implementation

import { createHash } from 'crypto';
import { v7 as uuidv7 } from 'uuid';

interface VCPConfig {
  policyId: string;
  conformanceTier: 'SILVER' | 'GOLD' | 'PLATINUM';
  anchorIntervalHours: number;
  useHashChain: boolean;
}

interface VCPEvent {
  header: {
    event_id: string;
    event_type: string;
    timestamp_iso: string;
    timestamp_int: string;
    timestamp_precision: string;
    clock_sync_status: string;
    vcp_version: string;
    hash_algo: string;
  };
  payload: Record<string, unknown>;
  policy_identification: {
    version: string;
    policy_id: string;
    conformance_tier: string;
    verification_depth: {
      hash_chain_validation: boolean;
      merkle_proof_required: boolean;
      external_anchor_required: boolean;
    };
  };
  security: {
    event_hash: string;
    prev_hash?: string;
  };
}

class MerkleTree {
  private leaves: Buffer[] = [];

  add(eventHash: string): void {
    const leaf = createHash('sha256')
      .update(Buffer.concat([Buffer.from([0x00]), Buffer.from(eventHash, 'hex')]))
      .digest();
    this.leaves.push(leaf);
  }

  get root(): string {
    if (this.leaves.length === 0) return '0'.repeat(64);

    let nodes = [...this.leaves];
    while (nodes.length > 1) {
      if (nodes.length % 2 === 1) nodes.push(nodes[nodes.length - 1]);
      const nextLevel: Buffer[] = [];
      for (let i = 0; i < nodes.length; i += 2) {
        const combined = createHash('sha256')
          .update(Buffer.concat([Buffer.from([0x01]), nodes[i], nodes[i + 1]]))
          .digest();
        nextLevel.push(combined);
      }
      nodes = nextLevel;
    }
    return nodes[0].toString('hex');
  }

  reset(): void {
    this.leaves = [];
  }
}

function canonicalize(obj: unknown): string {
  return JSON.stringify(obj, Object.keys(obj as object).sort());
}

class VCPClient {
  private config: VCPConfig;
  private tree: MerkleTree;
  private prevHash: string | null = null;
  private lastAnchor: Date | null = null;

  constructor(config: VCPConfig) {
    this.config = config;
    this.tree = new MerkleTree();
  }

  log(eventType: string, payload: Record<string, unknown>): VCPEvent {
    const now = new Date();

    const event: VCPEvent = {
      header: {
        event_id: uuidv7(),
        event_type: eventType,
        timestamp_iso: now.toISOString(),
        timestamp_int: now.getTime().toString(),
        timestamp_precision: 'MILLISECOND',
        clock_sync_status: 'BEST_EFFORT',
        vcp_version: '1.1',
        hash_algo: 'SHA256',
      },
      payload,
      policy_identification: {
        version: '1.1',
        policy_id: this.config.policyId,
        conformance_tier: this.config.conformanceTier,
        verification_depth: {
          hash_chain_validation: this.config.useHashChain,
          merkle_proof_required: true,
          external_anchor_required: true,
        },
      },
      security: {
        event_hash: '',
      },
    };

    // Compute hash
    const hashContent = canonicalize({ header: event.header, payload: event.payload });
    const eventHash = createHash('sha256').update(hashContent).digest('hex');
    event.security.event_hash = eventHash;

    if (this.config.useHashChain && this.prevHash) {
      event.security.prev_hash = this.prevHash;
    }

    this.tree.add(eventHash);
    this.prevHash = eventHash;

    return event;
  }

  anchor(): { merkleRoot: string; anchoredAt: string } {
    const root = this.tree.root;
    this.tree.reset();
    this.lastAnchor = new Date();

    return {
      merkleRoot: root,
      anchoredAt: this.lastAnchor.toISOString(),
    };
  }
}

// Usage
const client = new VCPClient({
  policyId: 'com.example:silver-trading-v1',
  conformanceTier: 'SILVER',
  anchorIntervalHours: 24,
  useHashChain: false,
});

const event = client.log('ORD', {
  trade_data: {
    order_id: 'ORD-001',
    symbol: 'XAUUSD',
    side: 'BUY',
    price: '2650.50',
  },
});

console.log('Logged:', event.header.event_id);
```

### 9.3 MQL5 Bridge Example

```mql5
//+------------------------------------------------------------------+
//| VCP v1.1 MQL5 Bridge - Silver Tier                               |
//+------------------------------------------------------------------+
#property copyright "VeritasChain Standards Organization"
#property version   "1.10"

#include <JAson.mqh>  // JSON library

input string VCP_PolicyID = "com.example:silver-mt5-ea";
input string VCP_SidecarURL = "http://localhost:8080/vcp/log";

//+------------------------------------------------------------------+
//| VCP Event Logger                                                  |
//+------------------------------------------------------------------+
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
    
    bool LogOrder(string orderId, string symbol, string side, 
                  string orderType, double price, double qty)
    {
        CJAVal event;
        
        // Header
        event["header"]["event_type"] = "ORD";
        event["header"]["timestamp_iso"] = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
        event["header"]["timestamp_int"] = IntegerToString(TimeCurrent() * 1000);
        event["header"]["vcp_version"] = "1.1";
        
        // Payload
        event["payload"]["trade_data"]["order_id"] = orderId;
        event["payload"]["trade_data"]["symbol"] = symbol;
        event["payload"]["trade_data"]["side"] = side;
        event["payload"]["trade_data"]["order_type"] = orderType;
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
    
    bool LogError(string errorType, string errorCode, string errorMsg, string severity)
    {
        CJAVal event;
        
        event["header"]["event_type"] = errorType;
        event["header"]["timestamp_iso"] = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
        event["header"]["timestamp_int"] = IntegerToString(TimeCurrent() * 1000);
        event["header"]["vcp_version"] = "1.1";
        
        event["payload"]["error_details"]["error_code"] = errorCode;
        event["payload"]["error_details"]["error_message"] = errorMsg;
        event["payload"]["error_details"]["severity"] = severity;
        
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

//+------------------------------------------------------------------+
//| Global VCP Logger Instance                                        |
//+------------------------------------------------------------------+
CVCPLogger* g_vcpLogger = NULL;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
    g_vcpLogger = new CVCPLogger(VCP_PolicyID, VCP_SidecarURL);
    
    // Log system initialization
    g_vcpLogger.LogError("INIT", "EA_START", "Expert Advisor initialized", "INFO");
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    if(g_vcpLogger != NULL)
    {
        g_vcpLogger.LogError("INIT", "EA_STOP", "Expert Advisor stopped", "INFO");
        delete g_vcpLogger;
    }
}

//+------------------------------------------------------------------+
//| Trade event handler                                               |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
{
    if(g_vcpLogger == NULL) return;
    
    if(trans.type == TRADE_TRANSACTION_ORDER_ADD)
    {
        g_vcpLogger.LogOrder(
            IntegerToString(trans.order),
            trans.symbol,
            (trans.order_type == ORDER_TYPE_BUY) ? "BUY" : "SELL",
            "MARKET",
            trans.price,
            trans.volume
        );
    }
    else if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
    {
        g_vcpLogger.LogExecution(
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

### 10.1 Compatibility Summary

| Feature | v1.0 | v1.1 | Action |
|---------|------|------|--------|
| Event Schema | Compatible | Extended | Add PolicyIdentification |
| Hash Chain | Required | Optional | No change needed |
| External Anchor (Silver) | Optional | **Required** | Must implement |
| Merkle Tree | Required | Required | No change |
| Signature | Required | Required | No change |

### 10.2 Step-by-Step Migration

#### Step 1: Add Policy Identification (REQUIRED)

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
    "policy_identification": {  # NEW
        "version": "1.1",
        "policy_id": "com.yourcompany:system-001",
        "conformance_tier": "SILVER",
        "verification_depth": {
            "hash_chain_validation": False,
            "merkle_proof_required": True,
            "external_anchor_required": True
        }
    },
    "security": {...}
}
```

#### Step 2: Add External Anchoring (Silver Tier)

```python
# Install OpenTimestamps
# pip install opentimestamps-client

import opentimestamps

class V11SilverClient(V10SilverClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_anchor = None
    
    def daily_anchor(self):
        """Anchor Merkle root to Bitcoin (REQUIRED in v1.1)."""
        root = self.merkle_tree.root
        
        # Create and submit timestamp
        timestamp = opentimestamps.stamp(bytes.fromhex(root))
        
        # Save proof
        proof_file = f"anchors/{datetime.now().strftime('%Y%m%d')}.ots"
        with open(proof_file, 'wb') as f:
            f.write(timestamp.serialize())
        
        self.last_anchor = datetime.now(timezone.utc)
        
        return {
            "merkle_root": root,
            "anchor_type": "OPENTIMESTAMPS",
            "proof_file": proof_file
        }
```

#### Step 3: (Optional) Remove Hash Chain

```python
# v1.0: prev_hash was REQUIRED
security = {
    "event_hash": event_hash,
    "prev_hash": self.prev_hash  # Was required
}

# v1.1: prev_hash is OPTIONAL
# You can remove it to simplify implementation
security = {
    "event_hash": event_hash
    # prev_hash omitted - perfectly valid in v1.1
}
```

### 10.3 Migration Checklist

```
[ ] Update vcp_version in header from "1.0" to "1.1"
[ ] Add policy_identification to all events
[ ] Define PolicyID following naming convention
[ ] Implement external anchoring (if Silver tier)
[ ] Update tests to validate new fields
[ ] (Optional) Remove hash chain if not needed
[ ] Run conformance test suite
[ ] Update documentation
```

---

## 11. Conformance Testing

### 11.1 v1.1 Test Requirements

| Test Category | Silver | Gold | Platinum |
|---------------|--------|------|----------|
| Schema Validation | Required | Required | Required |
| UUID v7 Format | Required | Required | Required |
| EventHash Calculation | Required | Required | Required |
| Hash Chain (PrevHash) | **Optional** | Optional | Optional |
| Merkle Tree | Required | Required | Required |
| Merkle Proof Verification | Required | Required | Required |
| **External Anchoring** | **Required** | Required | Required |
| **Policy Identification** | **Required** | Required | Required |
| Digital Signature | Required | Required | Required |
| Clock Sync (BEST_EFFORT) | Required | Required | Required |
| Clock Sync (NTP_SYNCED) | Optional | Required | Required |
| Clock Sync (PTP_LOCKED) | Optional | Optional | Required |

### 11.2 Critical Tests (v1.1)

Failure of any critical test results in automatic certification failure:

| Test ID | Description | v1.0 | v1.1 |
|---------|-------------|------|------|
| SCH-001 | Event structure validation | Critical | Critical |
| UID-001 | UUID v7 format | Critical | Critical |
| HCH-001 | Genesis event prev_hash | Critical | **Removed** |
| HCH-003 | Hash calculation | Critical | Critical |
| SIG-001 | Signature algorithm | Critical | Critical |
| **MKL-001** | Merkle tree construction | - | **Critical** |
| **MKL-002** | Merkle proof verification | - | **Critical** |
| **ANC-001** | External anchor existence | - | **Critical** |
| **POL-001** | Policy identification | - | **Critical** |

### 11.3 Running Conformance Tests

```bash
# Install test suite
pip install vcp-conformance-test

# Run tests for Silver tier
vcp-test --tier silver --version 1.1 ./your-implementation

# Run tests for Gold tier
vcp-test --tier gold --version 1.1 ./your-implementation

# Generate certification report
vcp-test --tier silver --version 1.1 --report ./your-implementation
```

---

## 12. Deployment Patterns

### 12.1 Sidecar Architecture

VCP operates as a **sidecar** - a non-invasive component running alongside existing systems.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EXISTING TRADING INFRASTRUCTURE                   │
│                         (NO MODIFICATIONS)                           │
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
| In-Process Hook | DLL/library integration | Silver (MT4/MT5) |
| Message Queue Tap | Subscribe to Kafka/Redis | Institutional |

### 12.3 Design Principles

| Principle | Description |
|-----------|-------------|
| **Non-invasive** | No changes to existing trading logic |
| **Fail-safe** | VCP failure MUST NOT impact trading |
| **Async-first** | Event capture should be asynchronous |
| **Idempotent** | Duplicate handling must be safe |
| **Recoverable** | Support replay after outages |

### 12.4 Deployment Checklist

```
[ ] Event capture point identified
[ ] Network/API access confirmed
[ ] Storage provisioned (local + anchor target)
[ ] Clock synchronization configured
[ ] Failover/recovery procedures documented
[ ] Performance impact measured (<1% latency target)
[ ] Key management procedures established
[ ] Monitoring and alerting configured
```

---

## 13. Appendices

### Appendix A: Complete Merkle Tree Implementation

```python
"""
Complete RFC 6962 Merkle Tree Implementation
"""

import hashlib
from typing import List, Tuple, Optional

class RFC6962MerkleTree:
    """
    RFC 6962 compliant Merkle Tree with audit path generation.
    """
    
    LEAF_PREFIX = b'\x00'
    NODE_PREFIX = b'\x01'
    
    def __init__(self):
        self.leaves: List[bytes] = []
        self._tree: List[List[bytes]] = []
    
    def add(self, data: bytes) -> int:
        """Add data and return leaf index."""
        leaf_hash = self._hash_leaf(data)
        self.leaves.append(leaf_hash)
        self._tree = []  # Invalidate cached tree
        return len(self.leaves) - 1
    
    def _hash_leaf(self, data: bytes) -> bytes:
        return hashlib.sha256(self.LEAF_PREFIX + data).digest()
    
    def _hash_node(self, left: bytes, right: bytes) -> bytes:
        return hashlib.sha256(self.NODE_PREFIX + left + right).digest()
    
    def _build_tree(self) -> List[List[bytes]]:
        if self._tree:
            return self._tree
        
        if not self.leaves:
            return [[]]
        
        tree = [self.leaves.copy()]
        
        while len(tree[-1]) > 1:
            level = tree[-1]
            if len(level) % 2 == 1:
                level = level + [level[-1]]
            
            next_level = []
            for i in range(0, len(level), 2):
                next_level.append(self._hash_node(level[i], level[i+1]))
            tree.append(next_level)
        
        self._tree = tree
        return tree
    
    @property
    def root(self) -> str:
        tree = self._build_tree()
        if not tree or not tree[-1]:
            return '0' * 64
        return tree[-1][0].hex()
    
    def get_audit_path(self, index: int) -> List[Tuple[str, str]]:
        """
        Get audit path for leaf at index.
        Returns list of (hash, position) tuples.
        Position is 'L' (left sibling) or 'R' (right sibling).
        """
        tree = self._build_tree()
        
        if index < 0 or index >= len(self.leaves):
            raise IndexError(f"Invalid leaf index: {index}")
        
        path = []
        idx = index
        
        for level in tree[:-1]:
            if len(level) == 1:
                break
            
            if idx % 2 == 0:
                sibling_idx = idx + 1
                position = 'R'
            else:
                sibling_idx = idx - 1
                position = 'L'
            
            if sibling_idx < len(level):
                path.append((level[sibling_idx].hex(), position))
            else:
                path.append((level[idx].hex(), 'R'))
            
            idx //= 2
        
        return path
    
    @staticmethod
    def verify_proof(
        leaf_data: bytes,
        audit_path: List[Tuple[str, str]],
        expected_root: str
    ) -> bool:
        """Verify that leaf_data is in tree with given root."""
        current = hashlib.sha256(b'\x00' + leaf_data).digest()
        
        for sibling_hex, position in audit_path:
            sibling = bytes.fromhex(sibling_hex)
            if position == 'L':
                current = hashlib.sha256(b'\x01' + sibling + current).digest()
            else:
                current = hashlib.sha256(b'\x01' + current + sibling).digest()
        
        return current.hex() == expected_root
```

### Appendix B: JSON Schema (v1.1)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://veritaschain.org/schemas/vcp-event-v1.1.json",
  "title": "VCP Event v1.1",
  "type": "object",
  "required": ["header", "payload", "policy_identification", "security"],
  "properties": {
    "header": {
      "type": "object",
      "required": ["event_id", "event_type", "timestamp_iso", "timestamp_int", "vcp_version"],
      "properties": {
        "event_id": {
          "type": "string",
          "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        },
        "event_type": {
          "type": "string",
          "enum": ["INIT", "SIG", "ORD", "ACK", "REJ", "EXE", "PRT", "CXL", "MOD", "CLS", 
                   "ERR_CONN", "ERR_AUTH", "ERR_TIMEOUT", "ERR_REJECT", "ERR_PARSE",
                   "ERR_SYNC", "ERR_RISK", "ERR_SYSTEM", "ERR_RECOVER"]
        },
        "timestamp_iso": { "type": "string", "format": "date-time" },
        "timestamp_int": { "type": "string", "pattern": "^[0-9]+$" },
        "timestamp_precision": {
          "type": "string",
          "enum": ["NANOSECOND", "MICROSECOND", "MILLISECOND"]
        },
        "clock_sync_status": {
          "type": "string",
          "enum": ["PTP_LOCKED", "NTP_SYNCED", "BEST_EFFORT", "UNRELIABLE"]
        },
        "vcp_version": { "type": "string", "const": "1.1" },
        "hash_algo": { "type": "string", "enum": ["SHA256", "SHA3_256", "BLAKE3"] }
      }
    },
    "payload": { "type": "object" },
    "policy_identification": {
      "type": "object",
      "required": ["version", "policy_id", "conformance_tier"],
      "properties": {
        "version": { "type": "string", "const": "1.1" },
        "policy_id": { "type": "string", "pattern": "^[a-z0-9.-]+:[a-zA-Z0-9_-]+$" },
        "conformance_tier": { "type": "string", "enum": ["SILVER", "GOLD", "PLATINUM"] },
        "verification_depth": {
          "type": "object",
          "properties": {
            "hash_chain_validation": { "type": "boolean" },
            "merkle_proof_required": { "type": "boolean", "const": true },
            "external_anchor_required": { "type": "boolean", "const": true }
          }
        }
      }
    },
    "security": {
      "type": "object",
      "required": ["event_hash"],
      "properties": {
        "event_hash": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
        "prev_hash": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
        "signature": { "type": "string" },
        "sign_algo": { "type": "string" },
        "merkle_root": { "type": "string", "pattern": "^[0-9a-f]{64}$" }
      }
    },
    "vcp_xref": {
      "type": "object",
      "properties": {
        "cross_reference_id": { "type": "string", "format": "uuid" },
        "party_role": { "type": "string", "enum": ["INITIATOR", "COUNTERPARTY", "OBSERVER"] },
        "counterparty_id": { "type": "string" },
        "reconciliation_status": { "type": "string", "enum": ["PENDING", "MATCHED", "DISCREPANCY", "TIMEOUT"] }
      }
    }
  }
}
```

### Appendix C: Implementation Checklist

#### Core Requirements (All Tiers)

```
[ ] UUID v7 event ID generation
[ ] Dual timestamp format (ISO + integer)
[ ] EventHash calculation (SHA-256)
[ ] Policy Identification in all events
[ ] Merkle tree construction (RFC 6962)
[ ] External anchoring implemented
[ ] Error event types supported
[ ] JSON canonicalization (RFC 8785)
```

#### Silver Tier Specific

```
[ ] MILLISECOND timestamp precision
[ ] BEST_EFFORT clock sync status
[ ] Daily (24h) external anchoring
[ ] OpenTimestamps or equivalent
```

#### Gold Tier Specific

```
[ ] MICROSECOND timestamp precision
[ ] NTP_SYNCED clock sync status
[ ] Hourly (1h) external anchoring
[ ] RFC 3161 TSA or equivalent
[ ] Ed25519 self-signing
[ ] Hash chain RECOMMENDED
```

#### Platinum Tier Specific

```
[ ] NANOSECOND timestamp precision
[ ] PTP_LOCKED clock sync status
[ ] 10-minute external anchoring
[ ] Blockchain or RFC 3161 TSA
[ ] HSM for key management
[ ] Performance: >1M events/sec
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.1.0 | 2025-12-30 | VSO Technical Committee | Initial v1.1 release |

---

## Contact

**VeritasChain Standards Organization (VSO)**

- Website: https://veritaschain.org
- GitHub: https://github.com/veritaschain
- Email: technical@veritaschain.org
- Standards: standards@veritaschain.org

---

*Copyright © 2025 VeritasChain Standards Organization. Licensed under Apache 2.0.*
