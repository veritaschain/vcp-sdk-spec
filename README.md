<p align="center">
  <img src="https://veritaschain.org/assets/img/logo.png" alt="VeritasChain Protocol" width="150"/>
</p>

<h1 align="center">VCP SDK Specification v1.1</h1>

<p align="center">
  <strong>SDK Interface Specification for VeritasChain Protocol</strong><br/>
  <em>TypeScript • Python • MQL5</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.1-blue?style=flat-square" alt="Version"/>
  <img src="https://img.shields.io/badge/Status-Release%20Candidate-yellow?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/License-Apache%202.0-green?style=flat-square" alt="License"/>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-supported-languages">Languages</a> •
  <a href="#-sdk-components">Components</a> •
  <a href="#-specification">Specification</a> •
  <a href="#-examples">Examples</a>
</p>

---

## 📚 Documentation

| Document | Version | Status |
|----------|---------|--------|
| [SDK Specification](./VCP_SDK_SPECIFICATION_v1_0_EN.md) | 1.0 | Release Candidate |
| [Implementation Guide](./VCP_IMPLEMENTATION_GUIDE_v1_1.md) | 1.1 | **Production Ready** |

## What's New in v1.1

- **External Anchoring**: REQUIRED for all tiers (including Silver)
- **Policy Identification**: REQUIRED field in all events
- **PrevHash**: Now OPTIONAL (simplifies implementation)
- **VCP-XREF**: Dual logging extension for multi-party verification
- **Error Events**: Standardized ERR_* event types

---

## 📖 Overview

This repository defines the **Software Development Kit (SDK) specification** for VeritasChain Protocol (VCP). It describes common data models, logging clients, and explorer clients for implementations in TypeScript, Python, and MQL5 bridge environments.

### What's Included

| Component | Description |
|-----------|-------------|
| **Event Model** | Unified VCP event structure (header, payload, security) |
| **Logger Client** | Interface for logging events to VeritasChain Cloud (VCC) |
| **Explorer Client** | Interface for querying events and verifying Merkle proofs |
| **Utility Functions** | UUID v7 generation, timestamp handling, canonicalization |

### Who This Is For

- 🛠️ **SDK maintainers** building client libraries
- 🏢 **Exchange/broker engineers** integrating VCP
- 🏦 **Prop firm developers** building sidecar services
- ✅ **Certification engineers** preparing VC-Certified test suites

---

## ⚡ Quick Start

### Try VCP Now (No SDK Installation Required)

You can experience VCP immediately by calling the Explorer API directly:

```bash
# Check system status
curl https://explorer.veritaschain.org/api/v1/system/status | jq

# Search events (requires API key)
curl -H "Authorization: Bearer $VCP_API_KEY" \
  "https://explorer.veritaschain.org/api/v1/events?limit=5" | jq

# Get Merkle proof
curl -H "Authorization: Bearer $VCP_API_KEY" \
  "https://explorer.veritaschain.org/api/v1/events/{event_id}/proof" | jq
```

### Python Example (Direct API Call)

```python
"""
quickstart.py - VCP in 2 minutes (no SDK required)
"""
import os
import hashlib
import httpx

API_BASE = "https://explorer.veritaschain.org/api/v1"
API_KEY = os.environ.get("VCP_API_KEY", "your-api-key")
headers = {"Authorization": f"Bearer {API_KEY}"}

# 1. Get recent events
response = httpx.get(f"{API_BASE}/events", headers=headers, params={"limit": 3})
events = response.json().get("events", [])

for event in events:
    h = event["header"]
    print(f"{h['event_type']} | {h['symbol']} | {h['event_id'][:20]}...")

# 2. Verify Merkle proof locally
if events:
    event_id = events[0]["header"]["event_id"]
    proof_response = httpx.get(f"{API_BASE}/events/{event_id}/proof", headers=headers)
    proof = proof_response.json()
    
    # Client-side verification (no server trust!)
    current = bytes.fromhex(proof["event_hash"])
    for step in proof.get("proof_path", []):
        sibling = bytes.fromhex(step["hash"])
        if step["position"] == "left":
            current = hashlib.sha256(sibling + current).digest()
        else:
            current = hashlib.sha256(current + sibling).digest()
    
    is_valid = current.hex() == proof["merkle_root"]
    print(f"\n{'✅ VERIFIED' if is_valid else '❌ FAILED'}: Merkle proof")
```

```bash
pip install httpx
python quickstart.py
```

### TypeScript Example

```typescript
// quickstart.ts
const API_BASE = 'https://explorer.veritaschain.org/api/v1';

async function main() {
  // Get system status (no auth required)
  const status = await fetch(`${API_BASE}/system/status`).then(r => r.json());
  console.log(`Total Events: ${status.total_events?.toLocaleString()}`);
  
  // Search events
  const events = await fetch(`${API_BASE}/events?limit=3`, {
    headers: { 'Authorization': `Bearer ${process.env.VCP_API_KEY}` }
  }).then(r => r.json());
  
  for (const event of events.events || []) {
    console.log(`${event.header.event_type} | ${event.header.symbol}`);
  }
}

main();
```

### When SDK Packages Are Available

```bash
# Python (coming soon)
pip install veritaschain

# TypeScript (coming soon)
npm install @veritaschain/sdk
```

---

## 🌐 Supported Languages

| Language | Target Environment | Tier Support |
|----------|-------------------|--------------|
| **TypeScript** | Node.js, Browser | Silver, Gold, Platinum |
| **Python** | Server-side, Data Science | Silver, Gold, Platinum |
| **MQL5** | MetaTrader 5 (via bridge) | Silver |

### Language-Specific Notes

#### TypeScript
- Node.js 18+ and modern browsers
- Full async/await support
- Browser-compatible Merkle verification

#### Python
- Python 3.10+
- Async mode with `asyncio`
- `httpx` for HTTP client

#### MQL5
- Sidecar bridge pattern (not native SDK)
- Async via timer-based queue
- Local caching for network failures
- See [vcp-sidecar-guide](https://github.com/veritaschain/vcp-sidecar-guide) for details

---

## 🧩 SDK Components

### 1. Event Model

All SDKs implement the same event structure:

```
VcpEvent
├── header: VcpHeader
│   ├── event_id: string (UUID v7)
│   ├── trace_id: string (UUID v7)
│   ├── timestamp_int: string (nanoseconds)
│   ├── timestamp_iso: string (ISO 8601)
│   ├── event_type: string (SIG, ORD, EXE, etc.)
│   ├── event_type_code: number (1-255)
│   ├── venue_id: string
│   ├── symbol: string
│   └── account_id: string (pseudonymized)
├── payload: VcpPayload
│   ├── vcp_trade?: VcpTrade
│   ├── vcp_risk?: VcpRisk
│   └── vcp_gov?: VcpGov
└── security: VcpSecurity
    ├── prev_hash: string
    ├── event_hash: string
    ├── hash_algo: string
    ├── signature?: string
    └── signer_id?: string
```

### 2. Logger Client

```typescript
interface VcpLogger {
  log(event: VcpEvent): Promise<void>;
  flush(): Promise<void>;
  getQueueSize(): number;
  isConnected(): boolean;
  close(): Promise<void>;
}
```

### 3. Explorer Client

```typescript
interface VcpExplorer {
  searchEvents(params: EventSearchParams): Promise<EventSearchResult>;
  getEventById(eventId: string): Promise<VcpEvent | null>;
  getMerkleProof(eventId: string): Promise<MerkleProof>;
  getEventCertificate(eventId: string): Promise<EventCertificate>;
  verifyMerkleProof(proof: MerkleProof): boolean;
}
```

### 4. Utility Functions

| Function | Description |
|----------|-------------|
| `generateUuidV7()` | Time-ordered UUID generation |
| `getCurrentTimestamp()` | Dual format (int + ISO) |
| `canonicalizeJson()` | RFC 8785 JSON canonicalization |
| `calculateEventHash()` | SHA-256/SHA3-256/BLAKE3 |
| `numericToString()` | Safe numeric conversion |

---

## 📋 Specification Document

The complete SDK specification is available in:

| Language | File |
|----------|------|
| 🇬🇧 English | [VCP_SDK_SPECIFICATION_v1_0_EN.md](./VCP_SDK_SPECIFICATION_v1_0_EN.md) |

### Contents

1. Introduction
2. Architecture Overview
3. Shared Concepts (Event Model, Timestamps, Hashing)
4. TypeScript SDK
5. Python SDK
6. MQL5 SDK (Bridge)
7. Error Handling
8. Security Considerations
9. Testing and Validation
10. Versioning

---

## 📝 Examples

### Event Type Reference

| Code | Type | Description | Module |
|------|------|-------------|--------|
| 1 | `SIG` | Trading signal | VCP-GOV |
| 2 | `ORD` | Order submitted | VCP-TRADE |
| 3 | `ACK` | Order acknowledged | VCP-TRADE |
| 4 | `EXE` | Order executed | VCP-TRADE |
| 5 | `CXL` | Order cancelled | VCP-TRADE |
| 6 | `REJ` | Order rejected | VCP-TRADE |
| 20 | `RSK` | Risk snapshot | VCP-RISK |
| 90 | `HBT` | Heartbeat | VCP-CORE |
| 91 | `ERR` | System error | VCP-CORE |

### Sample Event (Order)

```json
{
  "header": {
    "event_id": "01934e3a-7b2c-7f93-8f2a-1234567890ab",
    "trace_id": "01934e3a-0000-7f93-8f2a-000000000001",
    "timestamp_int": "1732492800123456789",
    "timestamp_iso": "2025-11-25T00:00:00.123456789Z",
    "event_type": "ORD",
    "event_type_code": 2,
    "venue_id": "MT5_LIVE",
    "symbol": "EURUSD",
    "account_id": "acc_hash_abc123"
  },
  "payload": {
    "vcp_trade": {
      "order_id": "ord_12345",
      "client_order_id": "my_strategy_001",
      "side": "BUY",
      "order_type": "LIMIT",
      "price": "1.08550",
      "quantity": "100000",
      "time_in_force": "GTC"
    }
  },
  "security": {
    "prev_hash": "a1b2c3d4e5f6...",
    "event_hash": "f6e5d4c3b2a1...",
    "hash_algo": "SHA256"
  }
}
```

### Sample Event (Risk Snapshot)

```json
{
  "header": {
    "event_id": "01934e3a-8b2c-7f93-8f2a-1234567890ab",
    "trace_id": "01934e3a-0000-7f93-8f2a-000000000002",
    "timestamp_int": "1732492860000000000",
    "timestamp_iso": "2025-11-25T00:01:00.000000000Z",
    "event_type": "RSK",
    "event_type_code": 20,
    "venue_id": "RISK_ENGINE",
    "symbol": "PORTFOLIO",
    "account_id": "acc_hash_abc123"
  },
  "payload": {
    "vcp_risk": {
      "snapshot_type": "PERIODIC",
      "pnl_realized": "1250.50",
      "pnl_unrealized": "-320.00",
      "var_1d": "5000.00",
      "max_drawdown": "0.08",
      "margin_used": "25000.00",
      "margin_available": "75000.00",
      "position_count": 5
    }
  },
  "security": {
    "prev_hash": "f6e5d4c3b2a1...",
    "event_hash": "1a2b3c4d5e6f...",
    "hash_algo": "SHA256"
  }
}
```

---

## 🏅 Tier Compatibility

| Tier | Timestamp Precision | Signature | SDK Requirements |
|------|---------------------|-----------|------------------|
| 🥈 **Silver** | MILLISECOND | Delegated (VCC) | Basic integration |
| 🥇 **Gold** | MICROSECOND | Self-signed Ed25519 | Key management |
| 🏆 **Platinum** | NANOSECOND | HSM-backed | PTP sync, HSM |

---

## 🔗 Related Repositories

| Repository | Description |
|------------|-------------|
| [vcp-spec](https://github.com/veritaschain/vcp-spec) | Core VCP specification |
| [vcp-explorer-api](https://github.com/veritaschain/vcp-explorer-api) | Explorer GUI & API |
| [vcp-sidecar-guide](https://github.com/veritaschain/vcp-sidecar-guide) | MT4/MT5/cTrader integration |
| [vcp-conformance-guide](https://github.com/veritaschain/vcp-conformance-guide) | Conformance tests |

---

## 🤝 Contributing

All changes to this specification should be proposed through **Issues** and **Pull Requests** so that implementations in all supported languages stay aligned.

We welcome:
- 📝 Implementation feedback
- 🐛 Bug reports
- 💡 Feature requests
- 🔧 Code contributions

---

## 📄 License

Apache License 2.0

---

## 📞 Contact

**VeritasChain Standards Organization (VSO)**

| Channel | Link |
|---------|------|
| Website | [veritaschain.org](https://veritaschain.org) |
| Email | [technical@veritaschain.org](mailto:technical@veritaschain.org) |
| GitHub | [github.com/veritaschain](https://github.com/veritaschain) |

---

<p align="center">
  <strong>VeritasChain Standards Organization</strong><br/>
  <em>"Verify, Don't Trust"</em>
</p>
