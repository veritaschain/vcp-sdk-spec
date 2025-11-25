# VeritasChain Protocol SDK Specification v1.0

**Document ID:** VSO-SDK-SPEC-001  
**Status:** Release Candidate  
**Version:** 1.0.0  
**Date:** 2025-11-25  
**Maintainer:** VeritasChain Standards Organization (VSO)  
**License:** Apache 2.0

---

## Abstract

This specification defines the standard SDK interface for VeritasChain Protocol (VCP) implementations across TypeScript, Python, and MQL5. The SDK enables developers to integrate VCP event logging, verification, and Merkle proof retrieval into algorithmic trading systems, prop firm platforms, and financial applications.

The SDK supports all three VCP compliance tiers (Silver, Gold, Platinum) and provides language-specific helpers for UUID v7 generation, numeric precision handling, and RFC 8785 JSON canonicalization.

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [Purpose](#11-purpose)
   - 1.2 [Scope](#12-scope)
   - 1.3 [Terminology](#13-terminology)
   - 1.4 [Conformance Language](#14-conformance-language)
2. [Architecture Overview](#2-architecture-overview)
   - 2.1 [SDK Components](#21-sdk-components)
   - 2.2 [Data Flow](#22-data-flow)
   - 2.3 [Tier Compatibility](#23-tier-compatibility)
3. [Shared Concepts](#3-shared-concepts)
   - 3.1 [Event Model](#31-event-model)
   - 3.2 [Event Type Codes](#32-event-type-codes)
   - 3.3 [Timestamp Handling](#33-timestamp-handling)
   - 3.4 [Numeric Precision](#34-numeric-precision)
   - 3.5 [Hashing and Canonicalization](#35-hashing-and-canonicalization)
   - 3.6 [Hash Chain Construction](#36-hash-chain-construction)
4. [TypeScript SDK](#4-typescript-sdk)
   - 4.1 [Package Information](#41-package-information)
   - 4.2 [Core Types](#42-core-types)
   - 4.3 [Logger Client](#43-logger-client)
   - 4.4 [Explorer Client](#44-explorer-client)
   - 4.5 [Utility Functions](#45-utility-functions)
   - 4.6 [Usage Examples](#46-usage-examples)
5. [Python SDK](#5-python-sdk)
   - 5.1 [Package Information](#51-package-information)
   - 5.2 [Core Classes](#52-core-classes)
   - 5.3 [Logger Client](#53-logger-client)
   - 5.4 [Explorer Client](#54-explorer-client)
   - 5.5 [Utility Functions](#55-utility-functions)
   - 5.6 [Usage Examples](#56-usage-examples)
6. [MQL5 SDK (vcp-mql-bridge)](#6-mql5-sdk-vcp-mql-bridge)
   - 6.1 [Purpose and Scope](#61-purpose-and-scope)
   - 6.2 [Architecture](#62-architecture)
   - 6.3 [Core Components](#63-core-components)
   - 6.4 [Configuration](#64-configuration)
   - 6.5 [Usage Patterns](#65-usage-patterns)
   - 6.6 [DLL Integration](#66-dll-integration)
7. [Error Handling](#7-error-handling)
   - 7.1 [Error Categories](#71-error-categories)
   - 7.2 [Error Codes](#72-error-codes)
   - 7.3 [Retry Policy](#73-retry-policy)
   - 7.4 [Offline Mode](#74-offline-mode)
8. [Security Considerations](#8-security-considerations)
   - 8.1 [API Key Management](#81-api-key-management)
   - 8.2 [Transport Security](#82-transport-security)
   - 8.3 [Data Privacy](#83-data-privacy)
9. [Testing and Validation](#9-testing-and-validation)
   - 9.1 [Unit Testing](#91-unit-testing)
   - 9.2 [Integration Testing](#92-integration-testing)
   - 9.3 [Conformance Testing](#93-conformance-testing)
10. [Versioning](#10-versioning)
    - 10.1 [Version Scheme](#101-version-scheme)
    - 10.2 [Compatibility Matrix](#102-compatibility-matrix)
11. [Appendices](#11-appendices)
    - Appendix A: [Complete Type Definitions](#appendix-a-complete-type-definitions)
    - Appendix B: [JSON Schema](#appendix-b-json-schema)
    - Appendix C: [Implementation Checklist](#appendix-c-implementation-checklist)
    - Appendix D: [Reference Documents](#appendix-d-reference-documents)

---

## 1. Introduction

### 1.1 Purpose

This specification defines a common SDK interface for client implementations of VeritasChain Protocol (VCP) across three primary programming languages:

- **TypeScript**: For web applications, Node.js services, and full-stack implementations
- **Python**: For quantitative trading systems, data science workflows, and backend services
- **MQL5**: For MetaTrader 5 Expert Advisors and indicators (via bridge pattern)

The SDK provides:

1. Canonical VCP event models (header, payload, security)
2. Logging client for sending events to VeritasChain Cloud (VCC)
3. Explorer client for querying, verification, and Merkle proofs
4. Language-specific helpers for UUID v7, numeric precision, and RFC 8785 JSON canonicalization

### 1.2 Scope

This specification covers:

- Core data structures and type definitions
- Logger client interface and behavior
- Explorer client interface and behavior
- Error handling and retry policies
- Security requirements
- Testing guidelines

This specification does NOT cover:

- VCC server-side implementation
- Blockchain anchoring mechanics (see VCP-SEC specification)
- Certification program requirements (see VC-Certified Program Guide)

### 1.3 Terminology

| Term | Definition |
|------|------------|
| **VCC** | VeritasChain Cloud - the hosted logging and verification infrastructure |
| **Event** | A single VCP record containing header, payload, and security sections |
| **TraceID** | UUID v7 identifier linking related events in a trade lifecycle |
| **Hash Chain** | Sequential linking of events via cryptographic hashes |
| **Merkle Proof** | Cryptographic proof of event inclusion in a Merkle tree |
| **Delegated Signature** | Signature performed by VCC on behalf of Silver Tier clients |
| **Sidecar** | Non-invasive integration pattern running alongside existing systems |

### 1.4 Conformance Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

---

## 2. Architecture Overview

### 2.1 SDK Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         VCP SDK                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Event      │  │  Logger     │  │  Explorer               │ │
│  │  Builder    │  │  Client     │  │  Client                 │ │
│  ├─────────────┤  ├─────────────┤  ├─────────────────────────┤ │
│  │ - Header    │  │ - log()     │  │ - searchEvents()        │ │
│  │ - Payload   │  │ - flush()   │  │ - getEventById()        │ │
│  │ - Security  │  │ - queue     │  │ - getMerkleProof()      │ │
│  │ - validate()│  │ - batch     │  │ - getEventCertificate() │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Utilities                                ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ - generateUuidV7()      - canonicalizeJson()                ││
│  │ - getCurrentTimestamp() - calculateEventHash()              ││
│  │ - numericToString()     - verifyMerkleProof()               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │    VeritasChain Cloud (VCC)   │
              │  ┌─────────┐  ┌────────────┐  │
              │  │ Logging │  │  Explorer  │  │
              │  │   API   │  │    API     │  │
              │  └─────────┘  └────────────┘  │
              └───────────────────────────────┘
```

### 2.2 Data Flow

```
[Trading System]
       │
       ▼
┌──────────────┐
│ Event Builder│ ──▶ Create VcpEvent with header + payload
└──────────────┘
       │
       ▼
┌──────────────┐
│ Logger Client│ ──▶ Queue → Batch → HTTP POST to VCC
└──────────────┘
       │
       ▼
┌──────────────┐
│     VCC      │ ──▶ Validate, Sign, Hash Chain, Merkle Tree
└──────────────┘
       │
       ▼
┌──────────────┐
│Explorer Client│ ◀── Query events, Verify proofs
└──────────────┘
```

### 2.3 Tier Compatibility

| Feature | Silver | Gold | Platinum |
|---------|--------|------|----------|
| Event Logging | ✓ | ✓ | ✓ |
| Delegated Signature | ✓ | ✗ | ✗ |
| Self-Signing | ✗ | ✓ | ✓ |
| Merkle Proof Retrieval | ✓ | ✓ | ✓ |
| Real-time WebSocket | ✗ | ✓ | ✓ |
| SBE Binary Format | ✗ | ✗ | ✓ |
| On-premise Deployment | ✗ | ✓ | ✓ |

---

## 3. Shared Concepts

### 3.1 Event Model

All SDKs MUST expose a common in-memory representation of a VCP Event with three sections:

```
VcpEvent
├── header      # VCP-CORE fields
│   ├── event_id           (UUID v7)
│   ├── trace_id           (UUID v7)
│   ├── timestamp_int      (string, nanoseconds)
│   ├── timestamp_iso      (ISO 8601)
│   ├── event_type         (enum string)
│   ├── event_type_code    (integer 1-255)
│   ├── timestamp_precision
│   ├── clock_sync_status
│   ├── hash_algo
│   ├── venue_id
│   ├── symbol
│   ├── account_id
│   └── operator_id        (optional)
│
├── payload     # Module-specific data
│   ├── trade_data         (VCP-TRADE)
│   ├── vcp_risk           (VCP-RISK)
│   ├── vcp_gov            (VCP-GOV)
│   ├── vcp_privacy        (VCP-PRIVACY)
│   └── vcp_recovery       (VCP-RECOVERY)
│
└── security    # Cryptographic fields
    ├── event_hash
    ├── prev_hash
    ├── signature          (optional for Silver)
    ├── sign_algo          (optional for Silver)
    ├── merkle_root        (populated by VCC)
    └── anchor             (populated by VCC)
```

**Requirements:**

- SDKs MUST use **UUID v7** for `event_id` and `trace_id`
- SDKs MAY accept UUID v4 for legacy import scenarios
- SDKs MUST represent timestamps in dual format (integer nanoseconds + ISO 8601)
- SDKs MUST enforce **numeric as string** for all financial values

### 3.2 Event Type Codes

SDKs MUST ship a fixed `EventType` enum mapping to VCP core codes:

| Code | Type | Category | Description |
|------|------|----------|-------------|
| 1 | SIG | Trade Lifecycle | Signal/decision generation |
| 2 | ORD | Trade Lifecycle | Order submission |
| 3 | ACK | Trade Lifecycle | Order acknowledgment |
| 4 | EXE | Trade Lifecycle | Full execution |
| 5 | PRT | Trade Lifecycle | Partial execution |
| 6 | REJ | Trade Lifecycle | Order rejection |
| 7 | CXL | Trade Lifecycle | Order cancellation |
| 8 | MOD | Trade Lifecycle | Order modification |
| 9 | CLS | Trade Lifecycle | Position close |
| 20 | ALG | Governance | Algorithm update |
| 21 | RSK | Governance | Risk parameter change |
| 22 | AUD | Governance | Audit event |
| 98 | HBT | System | Heartbeat |
| 99 | ERR | System | Error |
| 100 | REC | System | Recovery |
| 101 | SNC | System | Sync |

**IMPORTANT:** These codes are **immutable** for backward compatibility. Reserved ranges:

- 1-19: Trade lifecycle events
- 20-49: Governance events
- 50-89: Reserved for future use
- 90-99: System events
- 100-109: Recovery and sync events
- 110-255: Vendor extensions

### 3.3 Timestamp Handling

SDKs MUST provide dual timestamp representation:

```
timestamp_int: "1732492800000000000"  # Nanoseconds since Unix epoch (string)
timestamp_iso: "2025-11-25T00:00:00.000000000Z"  # ISO 8601 with nanoseconds
```

**Implementation Requirements:**

1. `timestamp_int` MUST be a **string** to preserve precision across all platforms
2. `timestamp_iso` MUST include timezone designator (Z or ±HH:MM)
3. SDKs MUST provide a utility function to generate both formats atomically:

```typescript
// TypeScript
function getCurrentTimestamp(): { timestamp_int: string; timestamp_iso: string }

# Python
def get_current_timestamp() -> tuple[str, str]
```

**Precision Levels:**

| Level | timestamp_int Length | Example |
|-------|---------------------|---------|
| NANOSECOND | 19 digits | "1732492800123456789" |
| MICROSECOND | 16 digits | "1732492800123456000" |
| MILLISECOND | 13 digits | "1732492800123000000" |

### 3.4 Numeric Precision

**CRITICAL:** All financial values MUST be represented as strings to avoid IEEE 754 floating-point precision loss.

**Affected Fields:**

- `price`, `quantity`, `executed_qty`, `remaining_qty`
- `execution_price`, `commission`, `slippage`
- `pnl_realized`, `pnl_unrealized`
- `var_1d`, `var_5d`, `max_drawdown`
- `margin_used`, `margin_available`
- All VCP-RISK snapshot values

**Example:**

```json
{
  "price": "1.23456789",
  "quantity": "100000.00",
  "commission": "0.0000035",
  "slippage": "-0.00002"
}
```

**SDK Enforcement:**

SDKs SHOULD provide a utility function to convert numeric types to strings:

```typescript
// TypeScript
function numericToString(value: number | bigint | string, precision?: number): string

# Python
def numeric_to_string(value: Union[int, float, Decimal, str], precision: int = None) -> str
```

SDKs SHOULD throw/raise an error if a `number` type is detected in financial fields during serialization.

### 3.5 Hashing and Canonicalization

All SDKs MUST provide:

#### 3.5.1 JSON Canonicalization

```typescript
function canonicalizeJson(obj: object): string
```

Implementation MUST follow RFC 8785:

- Deterministic key ordering (lexicographic Unicode code point order)
- No insignificant whitespace
- Specific number formatting (no exponential notation for integers)
- UTF-8 encoding without BOM

**Example:**

```javascript
// Input
{ "b": 2, "a": 1, "c": { "z": 26, "y": 25 } }

// Output (RFC 8785 canonical)
{"a":1,"b":2,"c":{"y":25,"z":26}}
```

#### 3.5.2 Event Hash Calculation

```typescript
function calculateEventHash(
  header: VcpHeader,
  payload: object,
  prevHash: string,
  algo?: 'SHA256' | 'SHA3_256' | 'BLAKE3'
): string
```

**Algorithm (as defined in VCP-SEC):**

1. Concatenate: `canonicalizeJson(header) + canonicalizeJson(payload) + prevHash`
2. Prepend version byte: `0x00` for SHA256, `0x01` for SHA3-256, `0x02` for BLAKE3
3. Hash the result
4. Return hex-encoded hash string

**Pseudocode:**

```
input = canonicalize(header) || canonicalize(payload) || prev_hash
prefix = version_byte[algo]
hash = HASH_FUNCTION(prefix || input)
return hex_encode(hash)
```

### 3.6 Hash Chain Construction

Events form an immutable chain through `prev_hash` linking:

```
Event 1 (Genesis)
├── event_hash: H1 = hash(header1 + payload1 + "0x00...00")
└── prev_hash: "0x00...00" (64 zeros)
                    │
                    ▼
Event 2
├── event_hash: H2 = hash(header2 + payload2 + H1)
└── prev_hash: H1
                    │
                    ▼
Event 3
├── event_hash: H3 = hash(header3 + payload3 + H2)
└── prev_hash: H2
```

**Genesis Event:** The first event in a chain MUST use `prev_hash = "0" * 64` (64 hex zeros).

---

## 4. TypeScript SDK

### 4.1 Package Information

| Attribute | Value |
|-----------|-------|
| Package Name | `@veritaschain/vcp-sdk` |
| Registry | npm |
| Runtime | Node.js 18+ / Browser (ES2020) |
| TypeScript | 5.0+ |
| License | Apache 2.0 |

**Installation:**

```bash
npm install @veritaschain/vcp-sdk
# or
yarn add @veritaschain/vcp-sdk
```

### 4.2 Core Types

#### 4.2.1 Enumerations

```typescript
/**
 * Supported hash algorithms
 */
export type HashAlgo = 'SHA256' | 'SHA3_256' | 'BLAKE3';

/**
 * Supported signature algorithms
 */
export type SignAlgo = 
  | 'ED25519' 
  | 'ECDSA_SECP256K1' 
  | 'RSA_2048' 
  | 'DILITHIUM2' 
  | 'FALCON512';

/**
 * Event type enumeration
 */
export type EventType = 
  | 'SIG' | 'ORD' | 'ACK' | 'EXE' | 'PRT' | 'REJ' | 'CXL' | 'MOD' | 'CLS'
  | 'ALG' | 'RSK' | 'AUD'
  | 'HBT' | 'ERR' | 'REC' | 'SNC';

/**
 * Event type code mapping
 */
export const EventTypeCode: Record<EventType, number> = {
  SIG: 1, ORD: 2, ACK: 3, EXE: 4, PRT: 5, REJ: 6, CXL: 7, MOD: 8, CLS: 9,
  ALG: 20, RSK: 21, AUD: 22,
  HBT: 98, ERR: 99, REC: 100, SNC: 101
} as const;

/**
 * Timestamp precision levels
 */
export type TimestampPrecision = 'NANOSECOND' | 'MICROSECOND' | 'MILLISECOND';

/**
 * Clock synchronization status
 */
export type ClockSyncStatus = 'PTP_LOCKED' | 'NTP_SYNCED' | 'BEST_EFFORT' | 'UNRELIABLE';

/**
 * Order side
 */
export type OrderSide = 'BUY' | 'SELL';

/**
 * Order type
 */
export type OrderType = 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';

/**
 * Algorithm type for VCP-GOV
 */
export type AlgoType = 'AI_MODEL' | 'RULE_BASED' | 'HYBRID';

/**
 * Explainability method for VCP-GOV
 */
export type ExplainabilityMethod = 'SHAP' | 'LIME' | 'GRADCAM' | 'RULE_TRACE';

/**
 * Risk classification
 */
export type RiskClassification = 'HIGH' | 'MEDIUM' | 'LOW';
```

#### 4.2.2 Header Interface

```typescript
/**
 * VCP Event Header (VCP-CORE)
 */
export interface VcpHeader {
  /** Unique event identifier (UUID v7) */
  event_id: string;
  
  /** Trade lifecycle tracking identifier (UUID v7) */
  trace_id: string;
  
  /** Timestamp as nanoseconds since Unix epoch (string for precision) */
  timestamp_int: string;
  
  /** Timestamp in ISO 8601 format */
  timestamp_iso: string;
  
  /** Event type name */
  event_type: EventType;
  
  /** Event type numeric code (1-255) */
  event_type_code: number;
  
  /** Timestamp precision level */
  timestamp_precision: TimestampPrecision;
  
  /** Clock synchronization status */
  clock_sync_status: ClockSyncStatus;
  
  /** Hash algorithm used */
  hash_algo: HashAlgo;
  
  /** Trading venue identifier (MIC code or custom) */
  venue_id: string;
  
  /** Trading symbol */
  symbol: string;
  
  /** Pseudonymized account identifier */
  account_id: string;
  
  /** Operator/trader identifier (optional) */
  operator_id?: string | null;
}
```

#### 4.2.3 Payload Interfaces

```typescript
/**
 * VCP-TRADE Payload
 */
export interface VcpTradePayload {
  /** Internal order identifier */
  order_id?: string;
  
  /** Broker-assigned order identifier */
  broker_order_id?: string;
  
  /** Exchange-assigned order identifier */
  exchange_order_id?: string;
  
  /** Order side */
  side?: OrderSide;
  
  /** Order type */
  order_type?: OrderType;
  
  /** Order price (string for precision) */
  price?: string;
  
  /** Order quantity (string for precision) */
  quantity?: string;
  
  /** Executed quantity (string for precision) */
  executed_qty?: string;
  
  /** Remaining quantity (string for precision) */
  remaining_qty?: string;
  
  /** Currency code (ISO 4217) */
  currency?: string;
  
  /** Execution price (string for precision) */
  execution_price?: string;
  
  /** Commission amount (string for precision) */
  commission?: string;
  
  /** Slippage amount (string for precision) */
  slippage?: string;
  
  /** Rejection reason code or message */
  reject_reason?: string;
  
  /** Time in force */
  time_in_force?: 'GTC' | 'IOC' | 'FOK' | 'DAY';
  
  /** Realized PnL (string for precision) */
  pnl_realized?: string;
  
  /** Unrealized PnL (string for precision) */
  pnl_unrealized?: string;
}

/**
 * VCP-RISK Payload
 */
export interface VcpRiskPayload {
  /** Risk metrics snapshot (all values as strings) */
  snapshot?: Record<string, string>;
  
  /** Triggered risk controls */
  triggered_controls?: Array<{
    /** Control name/identifier */
    control_name: string;
    
    /** Value that triggered the control (string) */
    trigger_value: string;
    
    /** Action taken */
    action: 'ALERT' | 'REDUCE' | 'LIQUIDATE' | 'HALT';
    
    /** Trigger timestamp (nanoseconds) */
    timestamp_int: string;
  }>;
}

/**
 * Feature contribution for explainability
 */
export interface FeatureContribution {
  /** Feature name */
  name: string;
  
  /** Feature value (string for precision) */
  value: string;
  
  /** Feature weight (string, optional) */
  weight?: string;
  
  /** Contribution to decision (string, optional) */
  contribution?: string;
}

/**
 * VCP-GOV Payload (Algorithm Governance)
 */
export interface VcpGovPayload {
  /** Algorithm identifier */
  algo_id?: string;
  
  /** Algorithm version */
  algo_version?: string;
  
  /** Algorithm type */
  algo_type?: AlgoType;
  
  /** Model file hash (for AI models) */
  model_hash?: string;
  
  /** Risk classification under EU AI Act */
  risk_classification?: RiskClassification;
  
  /** Last approval authority */
  last_approval_by?: string;
  
  /** Approval timestamp (nanoseconds) */
  approval_timestamp_int?: string;
  
  /** Link to testing records */
  testing_record_link?: string;
  
  /** Decision factors for explainability */
  decision_factors?: {
    /** Input features and contributions */
    features?: FeatureContribution[];
    
    /** Model confidence score (string, 0-1) */
    confidence_score?: string;
    
    /** Explainability method used */
    explainability_method?: ExplainabilityMethod;
  };
}

/**
 * VCP-PRIVACY Payload
 */
export interface VcpPrivacyPayload {
  /** Data retention policy */
  retention_policy?: string;
  
  /** Encryption key identifier */
  encryption_key_id?: string;
  
  /** Anonymization level */
  anonymization_level?: 'NONE' | 'PSEUDONYMIZED' | 'ANONYMIZED';
  
  /** GDPR lawful basis */
  gdpr_basis?: string;
}

/**
 * VCP-RECOVERY Payload
 */
export interface VcpRecoveryPayload {
  /** Recovery reason */
  reason?: 'CONNECTION_RESTORED' | 'MANUAL_SYNC' | 'SYSTEM_RESTART';
  
  /** Number of cached events being flushed */
  cached_event_count?: number;
  
  /** Cache start timestamp */
  cache_start_timestamp?: string;
  
  /** Cache end timestamp */
  cache_end_timestamp?: string;
  
  /** Gap detection results */
  gap_detection?: {
    expected_count: number;
    actual_count: number;
    missing_event_ids?: string[];
  };
}
```

#### 4.2.4 Security Interface

```typescript
/**
 * Blockchain anchor information
 */
export interface BlockchainAnchor {
  /** Blockchain network identifier */
  network: string;
  
  /** Transaction hash */
  tx_hash: string;
  
  /** Block number */
  block_number: number;
  
  /** Anchor timestamp (ISO 8601) */
  anchored_at: string;
}

/**
 * VCP-SEC Security Section
 */
export interface VcpSecurity {
  /** Hash of this event */
  event_hash: string;
  
  /** Hash of the previous event in chain */
  prev_hash: string;
  
  /** Digital signature (optional for Silver Tier) */
  signature?: string;
  
  /** Signature algorithm used */
  sign_algo?: SignAlgo;
  
  /** Merkle tree root (populated by VCC) */
  merkle_root?: string;
  
  /** Blockchain anchor information (populated by VCC) */
  anchor?: BlockchainAnchor;
}
```

#### 4.2.5 Complete Event Interface

```typescript
/**
 * Complete VCP Event
 */
export interface VcpEvent {
  /** Event header (VCP-CORE) */
  header: VcpHeader;
  
  /** Event payload (module-specific data) */
  payload: {
    trade_data?: VcpTradePayload;
    vcp_risk?: VcpRiskPayload;
    vcp_gov?: VcpGovPayload;
    vcp_privacy?: VcpPrivacyPayload;
    vcp_recovery?: VcpRecoveryPayload;
  };
  
  /** Security section (VCP-SEC) */
  security: VcpSecurity;
}
```

### 4.3 Logger Client

#### 4.3.1 Configuration

```typescript
/**
 * Logger client configuration
 */
export interface VcpLoggerConfig {
  /** VCC Logging API base URL */
  endpoint: string;
  
  /** API key for authentication */
  apiKey: string;
  
  /** Enable asynchronous mode (default: true) */
  asyncMode?: boolean;
  
  /** Maximum queue size before blocking (default: 10000) */
  queueSize?: number;
  
  /** Batch size for sending (default: 100) */
  batchSize?: number;
  
  /** Batch send interval in milliseconds (default: 1000) */
  batchIntervalMs?: number;
  
  /** Maximum retry attempts (default: 3) */
  retryCount?: number;
  
  /** Retry delay in milliseconds (default: 1000) */
  retryDelayMs?: number;
  
  /** Enable local cache for offline mode (default: false) */
  enableLocalCache?: boolean;
  
  /** Local cache file path (for Node.js) */
  localCachePath?: string;
  
  /** Request timeout in milliseconds (default: 30000) */
  timeoutMs?: number;
  
  /** Enable debug logging (default: false) */
  debug?: boolean;
}
```

#### 4.3.2 Interface

```typescript
/**
 * Logger client interface
 */
export interface VcpLogger {
  /**
   * Log a single event
   * @param event - VCP event to log
   * @returns Promise resolving when event is queued (async) or sent (sync)
   */
  log(event: VcpEvent): Promise<void>;
  
  /**
   * Flush all queued events immediately
   * @returns Promise resolving when all events are sent
   */
  flush(): Promise<void>;
  
  /**
   * Get current queue size
   * @returns Number of events waiting to be sent
   */
  getQueueSize(): number;
  
  /**
   * Check if logger is connected
   * @returns Connection status
   */
  isConnected(): boolean;
  
  /**
   * Close the logger and release resources
   */
  close(): Promise<void>;
}
```

#### 4.3.3 Factory Function

```typescript
/**
 * Create a new VCP Logger instance
 * @param config - Logger configuration
 * @returns Logger instance
 */
export function createLogger(config: VcpLoggerConfig): VcpLogger;
```

### 4.4 Explorer Client

#### 4.4.1 Configuration

```typescript
/**
 * Explorer client configuration
 */
export interface VcpExplorerConfig {
  /** VCC Explorer API base URL */
  endpoint: string;
  
  /** API key for authentication */
  apiKey: string;
  
  /** Request timeout in milliseconds (default: 30000) */
  timeoutMs?: number;
}
```

#### 4.4.2 Search Parameters

```typescript
/**
 * Event search parameters
 */
export interface EventSearchParams {
  /** Filter by trace ID */
  trace_id?: string;
  
  /** Filter by symbol */
  symbol?: string;
  
  /** Filter by event type */
  event_type?: EventType;
  
  /** Filter by event type code */
  event_type_code?: number;
  
  /** Filter by start time (ISO 8601) */
  start_time?: string;
  
  /** Filter by end time (ISO 8601) */
  end_time?: string;
  
  /** Filter by algorithm ID */
  algo_id?: string;
  
  /** Filter by venue ID */
  venue_id?: string;
  
  /** Filter by order ID */
  order_id?: string;
  
  /** Filter by account ID */
  account_id?: string;
  
  /** Maximum results (1-500, default: 50) */
  limit?: number;
  
  /** Pagination offset */
  offset?: number;
}
```

#### 4.4.3 Response Types

```typescript
/**
 * Merkle proof structure
 */
export interface MerkleProof {
  /** Event hash being proven */
  event_hash: string;
  
  /** Merkle root */
  merkle_root: string;
  
  /** Proof path (sibling hashes) */
  proof_path: Array<{
    hash: string;
    position: 'left' | 'right';
  }>;
  
  /** Tree size at proof generation */
  tree_size: number;
  
  /** Proof generation timestamp */
  generated_at: string;
}

/**
 * Event certificate
 */
export interface EventCertificate {
  /** Event being certified */
  event: VcpEvent;
  
  /** Merkle proof */
  proof: MerkleProof;
  
  /** Blockchain anchor (if available) */
  anchor?: BlockchainAnchor;
  
  /** Certificate generation timestamp */
  issued_at: string;
  
  /** Certificate issuer */
  issuer: string;
  
  /** Certificate signature */
  certificate_signature: string;
}

/**
 * Search result with pagination
 */
export interface EventSearchResult {
  /** Matching events */
  events: VcpEvent[];
  
  /** Total count (for pagination) */
  total_count: number;
  
  /** Has more results */
  has_more: boolean;
  
  /** Next offset for pagination */
  next_offset?: number;
}
```

#### 4.4.4 Interface

```typescript
/**
 * Explorer client interface
 */
export interface VcpExplorer {
  /**
   * Search for events
   * @param params - Search parameters
   * @returns Search result with events and pagination
   */
  searchEvents(params: EventSearchParams): Promise<EventSearchResult>;
  
  /**
   * Get a single event by ID
   * @param eventId - Event UUID
   * @returns Event or null if not found
   */
  getEventById(eventId: string): Promise<VcpEvent | null>;
  
  /**
   * Get Merkle proof for an event
   * @param eventId - Event UUID
   * @returns Merkle proof
   */
  getMerkleProof(eventId: string): Promise<MerkleProof>;
  
  /**
   * Get event certificate (includes proof and anchor)
   * @param eventId - Event UUID
   * @returns Event certificate
   */
  getEventCertificate(eventId: string): Promise<EventCertificate>;
  
  /**
   * Verify a Merkle proof locally
   * @param proof - Merkle proof to verify
   * @returns Verification result
   */
  verifyMerkleProof(proof: MerkleProof): boolean;
  
  /**
   * Get events by trace ID (trade lifecycle)
   * @param traceId - Trace UUID
   * @returns All events in the trade lifecycle
   */
  getEventsByTraceId(traceId: string): Promise<VcpEvent[]>;
}

/**
 * Create a new VCP Explorer instance
 * @param config - Explorer configuration
 * @returns Explorer instance
 */
export function createExplorer(config: VcpExplorerConfig): VcpExplorer;
```

### 4.5 Utility Functions

```typescript
/**
 * Generate a UUID v7
 * @returns UUID v7 string
 */
export function generateUuidV7(): string;

/**
 * Get current timestamp in dual format
 * @param precision - Timestamp precision (default: MILLISECOND)
 * @returns Object with timestamp_int and timestamp_iso
 */
export function getCurrentTimestamp(
  precision?: TimestampPrecision
): { timestamp_int: string; timestamp_iso: string };

/**
 * Convert numeric value to string with precision
 * @param value - Numeric value
 * @param precision - Decimal places (optional)
 * @returns String representation
 */
export function numericToString(
  value: number | bigint | string,
  precision?: number
): string;

/**
 * Canonicalize JSON per RFC 8785
 * @param obj - Object to canonicalize
 * @returns Canonical JSON string
 */
export function canonicalizeJson(obj: object): string;

/**
 * Calculate event hash
 * @param header - Event header
 * @param payload - Event payload
 * @param prevHash - Previous event hash
 * @param algo - Hash algorithm (default: SHA256)
 * @returns Hex-encoded hash string
 */
export function calculateEventHash(
  header: VcpHeader,
  payload: object,
  prevHash: string,
  algo?: HashAlgo
): string;

/**
 * Create a new VCP event with generated IDs and timestamps
 * @param eventType - Event type
 * @param options - Event options
 * @returns Partial VCP event (security section needs to be computed)
 */
export function createEvent(
  eventType: EventType,
  options: {
    traceId?: string;
    venueId: string;
    symbol: string;
    accountId: string;
    operatorId?: string;
    precision?: TimestampPrecision;
    clockSync?: ClockSyncStatus;
    hashAlgo?: HashAlgo;
  }
): Omit<VcpEvent, 'security'>;

/**
 * Pseudonymize account ID using SHA-256
 * @param accountId - Original account ID
 * @param salt - Salt for hashing
 * @returns Pseudonymized account ID
 */
export function pseudonymizeAccountId(accountId: string, salt: string): string;
```

### 4.6 Usage Examples

#### 4.6.1 Basic Event Logging

```typescript
import {
  createLogger,
  createEvent,
  calculateEventHash,
  EventTypeCode,
  type VcpEvent,
  type VcpTradePayload
} from '@veritaschain/vcp-sdk';

// Initialize logger
const logger = createLogger({
  endpoint: 'https://api.veritaschain.org/v1',
  apiKey: process.env.VCP_API_KEY!,
  asyncMode: true,
  batchSize: 50,
  batchIntervalMs: 1000
});

// Create a SIG event
const sigEvent = createEvent('SIG', {
  venueId: 'MT5-BROKER-X',
  symbol: 'EURUSD',
  accountId: 'acc_hashed_123',
  precision: 'MILLISECOND',
  clockSync: 'NTP_SYNCED'
});

// Add VCP-GOV payload
sigEvent.payload.vcp_gov = {
  algo_id: 'neural-scalper-v1.2',
  algo_version: '1.2.3',
  algo_type: 'AI_MODEL',
  model_hash: 'sha256:abc123...',
  risk_classification: 'HIGH',
  decision_factors: {
    features: [
      { name: 'rsi_14', value: '28.5', weight: '0.35', contribution: '0.12' },
      { name: 'ma_cross', value: '1', weight: '0.25', contribution: '0.08' }
    ],
    confidence_score: '0.87',
    explainability_method: 'SHAP'
  }
};

// Calculate security
const prevHash = '0'.repeat(64); // Genesis event
const eventHash = calculateEventHash(
  sigEvent.header,
  sigEvent.payload,
  prevHash
);

const fullEvent: VcpEvent = {
  ...sigEvent,
  security: {
    event_hash: eventHash,
    prev_hash: prevHash
  }
};

// Log the event
await logger.log(fullEvent);

// Ensure all events are sent before shutdown
await logger.flush();
await logger.close();
```

#### 4.6.2 Trade Lifecycle (SIG → ORD → EXE)

```typescript
import {
  createLogger,
  createExplorer,
  generateUuidV7,
  getCurrentTimestamp,
  calculateEventHash,
  numericToString,
  type VcpEvent
} from '@veritaschain/vcp-sdk';

const logger = createLogger({ /* config */ });

// Shared trace ID for the entire trade lifecycle
const traceId = generateUuidV7();
let prevHash = '0'.repeat(64);

// 1. Signal Event
const sigEvent: VcpEvent = {
  header: {
    event_id: generateUuidV7(),
    trace_id: traceId,
    ...getCurrentTimestamp('MILLISECOND'),
    event_type: 'SIG',
    event_type_code: 1,
    timestamp_precision: 'MILLISECOND',
    clock_sync_status: 'NTP_SYNCED',
    hash_algo: 'SHA256',
    venue_id: 'MT5-BROKER-X',
    symbol: 'XAUUSD',
    account_id: 'acc_123'
  },
  payload: {
    vcp_gov: {
      algo_id: 'gold-momentum-v2',
      decision_factors: {
        confidence_score: '0.92'
      }
    }
  },
  security: { event_hash: '', prev_hash: prevHash }
};

sigEvent.security.event_hash = calculateEventHash(
  sigEvent.header,
  sigEvent.payload,
  prevHash
);
await logger.log(sigEvent);
prevHash = sigEvent.security.event_hash;

// 2. Order Event
const ordEvent: VcpEvent = {
  header: {
    event_id: generateUuidV7(),
    trace_id: traceId,
    ...getCurrentTimestamp('MILLISECOND'),
    event_type: 'ORD',
    event_type_code: 2,
    timestamp_precision: 'MILLISECOND',
    clock_sync_status: 'NTP_SYNCED',
    hash_algo: 'SHA256',
    venue_id: 'MT5-BROKER-X',
    symbol: 'XAUUSD',
    account_id: 'acc_123'
  },
  payload: {
    trade_data: {
      order_id: '12345678',
      side: 'BUY',
      order_type: 'MARKET',
      price: numericToString(2650.50, 2),
      quantity: numericToString(1.0, 2)
    }
  },
  security: { event_hash: '', prev_hash: prevHash }
};

ordEvent.security.event_hash = calculateEventHash(
  ordEvent.header,
  ordEvent.payload,
  prevHash
);
await logger.log(ordEvent);
prevHash = ordEvent.security.event_hash;

// 3. Execution Event
const exeEvent: VcpEvent = {
  header: {
    event_id: generateUuidV7(),
    trace_id: traceId,
    ...getCurrentTimestamp('MILLISECOND'),
    event_type: 'EXE',
    event_type_code: 4,
    timestamp_precision: 'MILLISECOND',
    clock_sync_status: 'NTP_SYNCED',
    hash_algo: 'SHA256',
    venue_id: 'MT5-BROKER-X',
    symbol: 'XAUUSD',
    account_id: 'acc_123'
  },
  payload: {
    trade_data: {
      order_id: '12345678',
      broker_order_id: 'BRK-98765',
      side: 'BUY',
      execution_price: numericToString(2650.55, 2),
      executed_qty: numericToString(1.0, 2),
      commission: numericToString(7.50, 2),
      slippage: numericToString(0.05, 2)
    }
  },
  security: { event_hash: '', prev_hash: prevHash }
};

exeEvent.security.event_hash = calculateEventHash(
  exeEvent.header,
  exeEvent.payload,
  prevHash
);
await logger.log(exeEvent);

await logger.flush();
```

#### 4.6.3 Verification with Explorer

```typescript
import { createExplorer } from '@veritaschain/vcp-sdk';

const explorer = createExplorer({
  endpoint: 'https://api.veritaschain.org/v1',
  apiKey: process.env.VCP_API_KEY!
});

// Search by trace ID
const lifecycle = await explorer.getEventsByTraceId(traceId);
console.log(`Found ${lifecycle.length} events in trade lifecycle`);

// Get Merkle proof
const proof = await explorer.getMerkleProof(lifecycle[0].header.event_id);
console.log('Merkle root:', proof.merkle_root);

// Verify locally
const isValid = explorer.verifyMerkleProof(proof);
console.log('Proof valid:', isValid);

// Get full certificate
const cert = await explorer.getEventCertificate(lifecycle[0].header.event_id);
if (cert.anchor) {
  console.log('Anchored on:', cert.anchor.network);
  console.log('TX hash:', cert.anchor.tx_hash);
}
```

---

## 5. Python SDK

### 5.1 Package Information

| Attribute | Value |
|-----------|-------|
| Package Name | `vcp-sdk` |
| Registry | PyPI |
| Python | 3.10+ |
| License | Apache 2.0 |

**Installation:**

```bash
pip install vcp-sdk
# or
poetry add vcp-sdk
```

**Dependencies:**

- `httpx` >= 0.24.0 (async HTTP client)
- `pydantic` >= 2.0 (data validation)
- `cryptography` >= 41.0 (hashing and signatures)

### 5.2 Core Classes

#### 5.2.1 Enumerations

```python
from enum import Enum, IntEnum

class HashAlgo(str, Enum):
    SHA256 = "SHA256"
    SHA3_256 = "SHA3_256"
    BLAKE3 = "BLAKE3"

class SignAlgo(str, Enum):
    ED25519 = "ED25519"
    ECDSA_SECP256K1 = "ECDSA_SECP256K1"
    RSA_2048 = "RSA_2048"
    DILITHIUM2 = "DILITHIUM2"
    FALCON512 = "FALCON512"

class EventType(str, Enum):
    SIG = "SIG"
    ORD = "ORD"
    ACK = "ACK"
    EXE = "EXE"
    PRT = "PRT"
    REJ = "REJ"
    CXL = "CXL"
    MOD = "MOD"
    CLS = "CLS"
    ALG = "ALG"
    RSK = "RSK"
    AUD = "AUD"
    HBT = "HBT"
    ERR = "ERR"
    REC = "REC"
    SNC = "SNC"

class EventTypeCode(IntEnum):
    SIG = 1
    ORD = 2
    ACK = 3
    EXE = 4
    PRT = 5
    REJ = 6
    CXL = 7
    MOD = 8
    CLS = 9
    ALG = 20
    RSK = 21
    AUD = 22
    HBT = 98
    ERR = 99
    REC = 100
    SNC = 101

class TimestampPrecision(str, Enum):
    NANOSECOND = "NANOSECOND"
    MICROSECOND = "MICROSECOND"
    MILLISECOND = "MILLISECOND"

class ClockSyncStatus(str, Enum):
    PTP_LOCKED = "PTP_LOCKED"
    NTP_SYNCED = "NTP_SYNCED"
    BEST_EFFORT = "BEST_EFFORT"
    UNRELIABLE = "UNRELIABLE"

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class AlgoType(str, Enum):
    AI_MODEL = "AI_MODEL"
    RULE_BASED = "RULE_BASED"
    HYBRID = "HYBRID"

class RiskClassification(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
```

#### 5.2.2 Data Classes

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime

@dataclass
class VcpHeader:
    """VCP Event Header (VCP-CORE)"""
    event_id: str
    trace_id: str
    timestamp_int: str
    timestamp_iso: str
    event_type: EventType
    event_type_code: int
    timestamp_precision: TimestampPrecision
    clock_sync_status: ClockSyncStatus
    hash_algo: HashAlgo
    venue_id: str
    symbol: str
    account_id: str
    operator_id: Optional[str] = None

@dataclass
class VcpTradePayload:
    """VCP-TRADE Payload"""
    order_id: Optional[str] = None
    broker_order_id: Optional[str] = None
    exchange_order_id: Optional[str] = None
    side: Optional[OrderSide] = None
    order_type: Optional[OrderType] = None
    price: Optional[str] = None
    quantity: Optional[str] = None
    executed_qty: Optional[str] = None
    remaining_qty: Optional[str] = None
    currency: Optional[str] = None
    execution_price: Optional[str] = None
    commission: Optional[str] = None
    slippage: Optional[str] = None
    reject_reason: Optional[str] = None
    time_in_force: Optional[str] = None
    pnl_realized: Optional[str] = None
    pnl_unrealized: Optional[str] = None

@dataclass
class TriggeredControl:
    """Risk control trigger record"""
    control_name: str
    trigger_value: str
    action: str
    timestamp_int: str

@dataclass
class VcpRiskPayload:
    """VCP-RISK Payload"""
    snapshot: Optional[Dict[str, str]] = None
    triggered_controls: Optional[List[TriggeredControl]] = None

@dataclass
class FeatureContribution:
    """Feature contribution for explainability"""
    name: str
    value: str
    weight: Optional[str] = None
    contribution: Optional[str] = None

@dataclass
class DecisionFactors:
    """Decision factors for VCP-GOV"""
    features: Optional[List[FeatureContribution]] = None
    confidence_score: Optional[str] = None
    explainability_method: Optional[str] = None

@dataclass
class VcpGovPayload:
    """VCP-GOV Payload (Algorithm Governance)"""
    algo_id: Optional[str] = None
    algo_version: Optional[str] = None
    algo_type: Optional[AlgoType] = None
    model_hash: Optional[str] = None
    risk_classification: Optional[RiskClassification] = None
    last_approval_by: Optional[str] = None
    approval_timestamp_int: Optional[str] = None
    testing_record_link: Optional[str] = None
    decision_factors: Optional[DecisionFactors] = None

@dataclass
class BlockchainAnchor:
    """Blockchain anchor information"""
    network: str
    tx_hash: str
    block_number: int
    anchored_at: str

@dataclass
class VcpSecurity:
    """VCP-SEC Security Section"""
    event_hash: str
    prev_hash: str
    signature: Optional[str] = None
    sign_algo: Optional[SignAlgo] = None
    merkle_root: Optional[str] = None
    anchor: Optional[BlockchainAnchor] = None

@dataclass
class VcpPayload:
    """Combined event payload"""
    trade_data: Optional[VcpTradePayload] = None
    vcp_risk: Optional[VcpRiskPayload] = None
    vcp_gov: Optional[VcpGovPayload] = None
    vcp_privacy: Optional[Dict[str, Any]] = None
    vcp_recovery: Optional[Dict[str, Any]] = None

@dataclass
class VcpEvent:
    """Complete VCP Event"""
    header: VcpHeader
    payload: VcpPayload
    security: VcpSecurity
```

### 5.3 Logger Client

#### 5.3.1 Configuration

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class VcpLoggerConfig:
    """Logger client configuration"""
    endpoint: str
    api_key: str
    async_mode: bool = True
    queue_size: int = 10000
    batch_size: int = 100
    batch_interval_ms: int = 1000
    retry_count: int = 3
    retry_delay_ms: int = 1000
    enable_local_cache: bool = False
    local_cache_path: Optional[str] = None
    timeout_ms: int = 30000
    debug: bool = False
```

#### 5.3.2 Interface

```python
from abc import ABC, abstractmethod
from typing import List

class VcpLoggerInterface(ABC):
    """Abstract logger interface"""
    
    @abstractmethod
    def log(self, event: VcpEvent) -> None:
        """Log a single event"""
        pass
    
    @abstractmethod
    async def log_async(self, event: VcpEvent) -> None:
        """Log a single event asynchronously"""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush all queued events"""
        pass
    
    @abstractmethod
    async def flush_async(self) -> None:
        """Flush all queued events asynchronously"""
        pass
    
    @abstractmethod
    def get_queue_size(self) -> int:
        """Get current queue size"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the logger"""
        pass
```

#### 5.3.3 Implementation

```python
import asyncio
import queue
import threading
from typing import Optional
import httpx

class VcpLogger(VcpLoggerInterface):
    """VCP Logger client implementation"""
    
    def __init__(self, config: VcpLoggerConfig):
        self._config = config
        self._queue: queue.Queue[VcpEvent] = queue.Queue(maxsize=config.queue_size)
        self._connected = False
        self._shutdown = False
        self._client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None
        
        if config.async_mode:
            self._start_background_sender()
    
    def _start_background_sender(self) -> None:
        """Start background thread for batch sending"""
        self._sender_thread = threading.Thread(target=self._batch_sender, daemon=True)
        self._sender_thread.start()
    
    def _batch_sender(self) -> None:
        """Background batch sender"""
        batch: List[VcpEvent] = []
        
        while not self._shutdown:
            try:
                event = self._queue.get(timeout=self._config.batch_interval_ms / 1000)
                batch.append(event)
                
                if len(batch) >= self._config.batch_size:
                    self._send_batch(batch)
                    batch = []
            except queue.Empty:
                if batch:
                    self._send_batch(batch)
                    batch = []
    
    def _send_batch(self, batch: List[VcpEvent]) -> None:
        """Send a batch of events"""
        if not self._client:
            self._client = httpx.Client(
                timeout=self._config.timeout_ms / 1000,
                headers={"Authorization": f"Bearer {self._config.api_key}"}
            )
        
        payload = [self._event_to_dict(e) for e in batch]
        
        for attempt in range(self._config.retry_count):
            try:
                response = self._client.post(
                    f"{self._config.endpoint}/events/batch",
                    json=payload
                )
                response.raise_for_status()
                self._connected = True
                return
            except httpx.HTTPError as e:
                if attempt == self._config.retry_count - 1:
                    self._handle_send_error(batch, e)
                else:
                    import time
                    time.sleep(self._config.retry_delay_ms / 1000)
    
    def _event_to_dict(self, event: VcpEvent) -> dict:
        """Convert event to dictionary"""
        # Implementation details...
        pass
    
    def _handle_send_error(self, batch: List[VcpEvent], error: Exception) -> None:
        """Handle send error (cache locally if enabled)"""
        if self._config.enable_local_cache and self._config.local_cache_path:
            self._cache_events(batch)
    
    def _cache_events(self, events: List[VcpEvent]) -> None:
        """Cache events locally for later retry"""
        pass
    
    def log(self, event: VcpEvent) -> None:
        """Log a single event"""
        self._queue.put(event)
    
    async def log_async(self, event: VcpEvent) -> None:
        """Log a single event asynchronously"""
        await asyncio.get_event_loop().run_in_executor(None, self._queue.put, event)
    
    def flush(self) -> None:
        """Flush all queued events"""
        batch: List[VcpEvent] = []
        while not self._queue.empty():
            try:
                batch.append(self._queue.get_nowait())
            except queue.Empty:
                break
        
        if batch:
            self._send_batch(batch)
    
    async def flush_async(self) -> None:
        """Flush all queued events asynchronously"""
        await asyncio.get_event_loop().run_in_executor(None, self.flush)
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self._queue.qsize()
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self._connected
    
    def close(self) -> None:
        """Close the logger"""
        self._shutdown = True
        self.flush()
        if self._client:
            self._client.close()


def create_logger(config: VcpLoggerConfig) -> VcpLogger:
    """Factory function to create logger"""
    return VcpLogger(config)
```

### 5.4 Explorer Client

#### 5.4.1 Configuration

```python
@dataclass
class VcpExplorerConfig:
    """Explorer client configuration"""
    endpoint: str
    api_key: str
    timeout_ms: int = 30000
```

#### 5.4.2 Search Parameters

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class EventSearchParams:
    """Event search parameters"""
    trace_id: Optional[str] = None
    symbol: Optional[str] = None
    event_type: Optional[EventType] = None
    event_type_code: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    algo_id: Optional[str] = None
    venue_id: Optional[str] = None
    order_id: Optional[str] = None
    account_id: Optional[str] = None
    limit: int = 50
    offset: int = 0
```

#### 5.4.3 Response Types

```python
@dataclass
class ProofPath:
    """Merkle proof path element"""
    hash: str
    position: str  # 'left' or 'right'

@dataclass
class MerkleProof:
    """Merkle proof structure"""
    event_hash: str
    merkle_root: str
    proof_path: List[ProofPath]
    tree_size: int
    generated_at: str

@dataclass
class EventCertificate:
    """Event certificate"""
    event: VcpEvent
    proof: MerkleProof
    anchor: Optional[BlockchainAnchor]
    issued_at: str
    issuer: str
    certificate_signature: str

@dataclass
class EventSearchResult:
    """Search result with pagination"""
    events: List[VcpEvent]
    total_count: int
    has_more: bool
    next_offset: Optional[int]
```

#### 5.4.4 Interface

```python
class VcpExplorer:
    """VCP Explorer client"""
    
    def __init__(self, config: VcpExplorerConfig):
        self._config = config
        self._client = httpx.Client(
            timeout=config.timeout_ms / 1000,
            headers={"Authorization": f"Bearer {config.api_key}"}
        )
    
    def search_events(self, params: EventSearchParams) -> EventSearchResult:
        """Search for events"""
        query_params = {k: v for k, v in vars(params).items() if v is not None}
        response = self._client.get(
            f"{self._config.endpoint}/events",
            params=query_params
        )
        response.raise_for_status()
        data = response.json()
        return EventSearchResult(
            events=[self._parse_event(e) for e in data['events']],
            total_count=data['total_count'],
            has_more=data['has_more'],
            next_offset=data.get('next_offset')
        )
    
    def get_event_by_id(self, event_id: str) -> Optional[VcpEvent]:
        """Get a single event by ID"""
        response = self._client.get(f"{self._config.endpoint}/events/{event_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self._parse_event(response.json())
    
    def get_merkle_proof(self, event_id: str) -> MerkleProof:
        """Get Merkle proof for an event"""
        response = self._client.get(
            f"{self._config.endpoint}/events/{event_id}/proof"
        )
        response.raise_for_status()
        data = response.json()
        return MerkleProof(
            event_hash=data['event_hash'],
            merkle_root=data['merkle_root'],
            proof_path=[ProofPath(**p) for p in data['proof_path']],
            tree_size=data['tree_size'],
            generated_at=data['generated_at']
        )
    
    def get_event_certificate(self, event_id: str) -> EventCertificate:
        """Get event certificate"""
        response = self._client.get(
            f"{self._config.endpoint}/events/{event_id}/certificate"
        )
        response.raise_for_status()
        data = response.json()
        return EventCertificate(
            event=self._parse_event(data['event']),
            proof=MerkleProof(**data['proof']),
            anchor=BlockchainAnchor(**data['anchor']) if data.get('anchor') else None,
            issued_at=data['issued_at'],
            issuer=data['issuer'],
            certificate_signature=data['certificate_signature']
        )
    
    def verify_merkle_proof(self, proof: MerkleProof) -> bool:
        """Verify a Merkle proof locally"""
        current_hash = proof.event_hash
        
        for path_element in proof.proof_path:
            if path_element.position == 'left':
                current_hash = self._hash_pair(path_element.hash, current_hash)
            else:
                current_hash = self._hash_pair(current_hash, path_element.hash)
        
        return current_hash == proof.merkle_root
    
    def get_events_by_trace_id(self, trace_id: str) -> List[VcpEvent]:
        """Get all events in a trade lifecycle"""
        result = self.search_events(EventSearchParams(
            trace_id=trace_id,
            limit=500
        ))
        return result.events
    
    def _parse_event(self, data: dict) -> VcpEvent:
        """Parse event from JSON"""
        # Implementation details...
        pass
    
    def _hash_pair(self, left: str, right: str) -> str:
        """Hash two values together for Merkle tree"""
        import hashlib
        combined = bytes.fromhex(left) + bytes.fromhex(right)
        return hashlib.sha256(combined).hexdigest()
    
    def close(self) -> None:
        """Close the client"""
        self._client.close()


def create_explorer(config: VcpExplorerConfig) -> VcpExplorer:
    """Factory function to create explorer"""
    return VcpExplorer(config)
```

### 5.5 Utility Functions

```python
import uuid
import time
import hashlib
import json
from datetime import datetime, timezone
from typing import Tuple, Union
from decimal import Decimal

def generate_uuid_v7() -> str:
    """
    Generate a UUID v7 (time-ordered UUID)
    
    Returns:
        UUID v7 string
    """
    # Get current timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)
    
    # UUID v7 format: 48-bit timestamp | 4-bit version | 12-bit random | 62-bit random
    uuid_int = (timestamp_ms << 80) | (7 << 76) | (uuid.uuid4().int & ((1 << 76) - 1))
    
    return str(uuid.UUID(int=uuid_int))


def get_current_timestamp(
    precision: TimestampPrecision = TimestampPrecision.MILLISECOND
) -> Tuple[str, str]:
    """
    Get current timestamp in dual format
    
    Args:
        precision: Timestamp precision level
    
    Returns:
        Tuple of (timestamp_int, timestamp_iso)
    """
    now = datetime.now(timezone.utc)
    
    if precision == TimestampPrecision.NANOSECOND:
        # Python's datetime doesn't support true nanoseconds
        timestamp_ns = int(now.timestamp() * 1_000_000_000)
        iso_format = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond:06d}000Z"
    elif precision == TimestampPrecision.MICROSECOND:
        timestamp_ns = int(now.timestamp() * 1_000_000) * 1000
        iso_format = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond:06d}Z"
    else:  # MILLISECOND
        timestamp_ns = int(now.timestamp() * 1_000) * 1_000_000
        iso_format = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
    
    return str(timestamp_ns), iso_format


def numeric_to_string(
    value: Union[int, float, Decimal, str],
    precision: int = None
) -> str:
    """
    Convert numeric value to string with precision
    
    Args:
        value: Numeric value
        precision: Decimal places (optional)
    
    Returns:
        String representation
    """
    if isinstance(value, str):
        return value
    
    if isinstance(value, Decimal):
        if precision is not None:
            return f"{value:.{precision}f}"
        return str(value)
    
    if precision is not None:
        return f"{value:.{precision}f}"
    
    return str(value)


def canonicalize_json(obj: dict) -> str:
    """
    Canonicalize JSON per RFC 8785
    
    Args:
        obj: Object to canonicalize
    
    Returns:
        Canonical JSON string
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    )


def calculate_event_hash(
    header: VcpHeader,
    payload: VcpPayload,
    prev_hash: str,
    algo: HashAlgo = HashAlgo.SHA256
) -> str:
    """
    Calculate event hash
    
    Args:
        header: Event header
        payload: Event payload
        prev_hash: Previous event hash
        algo: Hash algorithm
    
    Returns:
        Hex-encoded hash string
    """
    header_dict = vars(header)
    payload_dict = _payload_to_dict(payload)
    
    canonical = canonicalize_json(header_dict) + canonicalize_json(payload_dict) + prev_hash
    
    # Version prefix
    if algo == HashAlgo.SHA256:
        prefix = b'\x00'
        hasher = hashlib.sha256()
    elif algo == HashAlgo.SHA3_256:
        prefix = b'\x01'
        hasher = hashlib.sha3_256()
    else:  # BLAKE3
        prefix = b'\x02'
        import blake3
        hasher = blake3.blake3()
    
    hasher.update(prefix + canonical.encode('utf-8'))
    return hasher.hexdigest()


def _payload_to_dict(payload: VcpPayload) -> dict:
    """Convert payload to dictionary, excluding None values"""
    result = {}
    for field_name in ['trade_data', 'vcp_risk', 'vcp_gov', 'vcp_privacy', 'vcp_recovery']:
        field_value = getattr(payload, field_name)
        if field_value is not None:
            if hasattr(field_value, '__dict__'):
                result[field_name] = {k: v for k, v in vars(field_value).items() if v is not None}
            else:
                result[field_name] = field_value
    return result


def pseudonymize_account_id(account_id: str, salt: str) -> str:
    """
    Pseudonymize account ID using SHA-256
    
    Args:
        account_id: Original account ID
        salt: Salt for hashing
    
    Returns:
        Pseudonymized account ID with 'acc_' prefix
    """
    hash_input = f"{salt}:{account_id}".encode('utf-8')
    hash_value = hashlib.sha256(hash_input).hexdigest()[:16]
    return f"acc_{hash_value}"
```

### 5.6 Usage Examples

#### 5.6.1 Basic Event Logging

```python
import os
from vcp_sdk import (
    create_logger,
    VcpLoggerConfig,
    VcpEvent,
    VcpHeader,
    VcpPayload,
    VcpSecurity,
    VcpGovPayload,
    DecisionFactors,
    FeatureContribution,
    EventType,
    EventTypeCode,
    TimestampPrecision,
    ClockSyncStatus,
    HashAlgo,
    AlgoType,
    generate_uuid_v7,
    get_current_timestamp,
    calculate_event_hash
)

# Initialize logger
config = VcpLoggerConfig(
    endpoint="https://api.veritaschain.org/v1",
    api_key=os.environ["VCP_API_KEY"],
    async_mode=True,
    batch_size=50
)
logger = create_logger(config)

# Generate IDs and timestamps
event_id = generate_uuid_v7()
trace_id = generate_uuid_v7()
timestamp_int, timestamp_iso = get_current_timestamp(TimestampPrecision.MILLISECOND)

# Create header
header = VcpHeader(
    event_id=event_id,
    trace_id=trace_id,
    timestamp_int=timestamp_int,
    timestamp_iso=timestamp_iso,
    event_type=EventType.SIG,
    event_type_code=EventTypeCode.SIG,
    timestamp_precision=TimestampPrecision.MILLISECOND,
    clock_sync_status=ClockSyncStatus.NTP_SYNCED,
    hash_algo=HashAlgo.SHA256,
    venue_id="MT5-BROKER-X",
    symbol="EURUSD",
    account_id="acc_hashed_123"
)

# Create payload with VCP-GOV
payload = VcpPayload(
    vcp_gov=VcpGovPayload(
        algo_id="neural-scalper-v1.2",
        algo_version="1.2.3",
        algo_type=AlgoType.AI_MODEL,
        model_hash="sha256:abc123...",
        decision_factors=DecisionFactors(
            features=[
                FeatureContribution(name="rsi_14", value="28.5", weight="0.35"),
                FeatureContribution(name="ma_cross", value="1", weight="0.25")
            ],
            confidence_score="0.87",
            explainability_method="SHAP"
        )
    )
)

# Calculate hash
prev_hash = "0" * 64  # Genesis event
event_hash = calculate_event_hash(header, payload, prev_hash)

# Create security section
security = VcpSecurity(
    event_hash=event_hash,
    prev_hash=prev_hash
)

# Create complete event
event = VcpEvent(header=header, payload=payload, security=security)

# Log the event
logger.log(event)

# Flush and close
logger.flush()
logger.close()
```

#### 5.6.2 Trade Lifecycle (SIG → ORD → EXE)

```python
from vcp_sdk import (
    create_logger, create_explorer,
    VcpLoggerConfig, VcpExplorerConfig,
    VcpEvent, VcpHeader, VcpPayload, VcpSecurity,
    VcpTradePayload, VcpGovPayload,
    EventType, EventTypeCode,
    generate_uuid_v7, get_current_timestamp,
    calculate_event_hash, numeric_to_string
)

logger = create_logger(VcpLoggerConfig(
    endpoint="https://api.veritaschain.org/v1",
    api_key=os.environ["VCP_API_KEY"]
))

# Shared trace ID
trace_id = generate_uuid_v7()
prev_hash = "0" * 64

def create_event(
    event_type: EventType,
    payload: VcpPayload,
    prev: str
) -> VcpEvent:
    ts_int, ts_iso = get_current_timestamp()
    header = VcpHeader(
        event_id=generate_uuid_v7(),
        trace_id=trace_id,
        timestamp_int=ts_int,
        timestamp_iso=ts_iso,
        event_type=event_type,
        event_type_code=getattr(EventTypeCode, event_type.value),
        timestamp_precision=TimestampPrecision.MILLISECOND,
        clock_sync_status=ClockSyncStatus.NTP_SYNCED,
        hash_algo=HashAlgo.SHA256,
        venue_id="MT5-BROKER-X",
        symbol="XAUUSD",
        account_id="acc_123"
    )
    
    event_hash = calculate_event_hash(header, payload, prev)
    security = VcpSecurity(event_hash=event_hash, prev_hash=prev)
    
    return VcpEvent(header=header, payload=payload, security=security)

# 1. SIG Event
sig_payload = VcpPayload(
    vcp_gov=VcpGovPayload(
        algo_id="gold-momentum-v2",
        decision_factors=DecisionFactors(confidence_score="0.92")
    )
)
sig_event = create_event(EventType.SIG, sig_payload, prev_hash)
logger.log(sig_event)
prev_hash = sig_event.security.event_hash

# 2. ORD Event
ord_payload = VcpPayload(
    trade_data=VcpTradePayload(
        order_id="12345678",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=numeric_to_string(2650.50, 2),
        quantity=numeric_to_string(1.0, 2)
    )
)
ord_event = create_event(EventType.ORD, ord_payload, prev_hash)
logger.log(ord_event)
prev_hash = ord_event.security.event_hash

# 3. EXE Event
exe_payload = VcpPayload(
    trade_data=VcpTradePayload(
        order_id="12345678",
        broker_order_id="BRK-98765",
        execution_price=numeric_to_string(2650.55, 2),
        executed_qty=numeric_to_string(1.0, 2),
        commission=numeric_to_string(7.50, 2),
        slippage=numeric_to_string(0.05, 2)
    )
)
exe_event = create_event(EventType.EXE, exe_payload, prev_hash)
logger.log(exe_event)

logger.flush()
logger.close()

# Verify with Explorer
explorer = create_explorer(VcpExplorerConfig(
    endpoint="https://api.veritaschain.org/v1",
    api_key=os.environ["VCP_API_KEY"]
))

lifecycle = explorer.get_events_by_trace_id(trace_id)
print(f"Found {len(lifecycle)} events in trade lifecycle")

for event in lifecycle:
    proof = explorer.get_merkle_proof(event.header.event_id)
    is_valid = explorer.verify_merkle_proof(proof)
    print(f"{event.header.event_type}: hash={event.security.event_hash[:16]}... valid={is_valid}")

explorer.close()
```

---

## 6. MQL5 SDK (vcp-mql-bridge)

### 6.1 Purpose and Scope

The MQL5 SDK is designed as a **Sidecar Bridge** rather than a full SDK. It enables MetaTrader 5 Expert Advisors (EAs) and Indicators to generate and send VCP events to VeritasChain Cloud without modifying the core trading logic.

**Key Characteristics:**

- Lightweight integration for retail trading environments
- Asynchronous event sending to avoid trading latency
- Local caching for network disconnection scenarios
- Compatible with Silver Tier requirements

### 6.2 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MetaTrader 5                             │
│  ┌───────────────┐                                          │
│  │    EA/Indicator│                                          │
│  │  (Trading Logic)│                                         │
│  └───────┬───────┘                                          │
│          │ Hook Points                                       │
│          ▼                                                   │
│  ┌───────────────┐     ┌───────────────┐                    │
│  │ vcp-mql-bridge│────▶│  Local Queue  │                    │
│  │   (VCPLogger) │     │  (Memory/File)│                    │
│  └───────────────┘     └───────┬───────┘                    │
│                                │                             │
│                        ┌───────▼───────┐                    │
│                        │   Timer Send  │                    │
│                        │  (Background) │                    │
│                        └───────┬───────┘                    │
└────────────────────────────────┼────────────────────────────┘
                                 │ HTTPS
                                 ▼
                    ┌────────────────────────┐
                    │  VeritasChain Cloud    │
                    │     (VCC API)          │
                    └────────────────────────┘
```

### 6.3 Core Components

#### 6.3.1 Main Include File

```cpp
//+------------------------------------------------------------------+
//|                                                    VCPLogger.mqh |
//|                        VeritasChain Protocol SDK for MQL5        |
//|                              Version 1.0.0                        |
//+------------------------------------------------------------------+
#property copyright "VeritasChain Standards Organization"
#property version   "1.0.0"
#property strict

//--- Enumerations
enum ENUM_VCP_EVENT_TYPE {
    VCP_SIG = 1,
    VCP_ORD = 2,
    VCP_ACK = 3,
    VCP_EXE = 4,
    VCP_PRT = 5,
    VCP_REJ = 6,
    VCP_CXL = 7,
    VCP_MOD = 8,
    VCP_CLS = 9,
    VCP_ALG = 20,
    VCP_RSK = 21,
    VCP_AUD = 22,
    VCP_HBT = 98,
    VCP_ERR = 99,
    VCP_REC = 100,
    VCP_SNC = 101
};

enum ENUM_VCP_CLOCK_SYNC {
    VCP_CLOCK_PTP_LOCKED,
    VCP_CLOCK_NTP_SYNCED,
    VCP_CLOCK_BEST_EFFORT,
    VCP_CLOCK_UNRELIABLE
};

enum ENUM_VCP_ORDER_SIDE {
    VCP_SIDE_BUY,
    VCP_SIDE_SELL
};

enum ENUM_VCP_ORDER_TYPE {
    VCP_TYPE_MARKET,
    VCP_TYPE_LIMIT,
    VCP_TYPE_STOP,
    VCP_TYPE_STOP_LIMIT
};

//--- Configuration structure
struct VCPConfig {
    string   api_key;
    string   endpoint;
    string   venue_id;
    bool     async_mode;
    int      queue_size;
    int      batch_size;
    int      batch_interval_ms;
    int      retry_count;
    int      retry_delay_ms;
    bool     enable_local_cache;
    string   cache_file_path;
    bool     debug;
    ENUM_VCP_CLOCK_SYNC clock_sync;
};

//--- Event data structure
struct VCPEventData {
    string   event_id;
    string   trace_id;
    string   timestamp_int;
    string   timestamp_iso;
    int      event_type_code;
    string   symbol;
    string   account_id;
    string   order_id;
    string   side;
    string   order_type;
    string   price;
    string   quantity;
    string   exec_price;
    string   exec_qty;
    string   commission;
    string   slippage;
    string   reject_reason;
    string   algo_id;
    string   algo_version;
    string   confidence_score;
    string   gov_data_json;
    string   risk_data_json;
    string   error_code;
    string   error_message;
};
```

#### 6.3.2 Logger Class

```cpp
//+------------------------------------------------------------------+
//|                           VCPLogger Class                         |
//+------------------------------------------------------------------+
class VCPLogger {
private:
    VCPConfig      m_config;
    VCPEventData   m_queue[];
    int            m_queue_head;
    int            m_queue_tail;
    int            m_queue_count;
    bool           m_initialized;
    string         m_prev_hash;
    datetime       m_last_send_time;
    
    //--- Internal methods
    string         GenerateUuidV7();
    string         GetCurrentTimestampInt();
    string         GetCurrentTimestampIso();
    string         CalculateEventHash(const VCPEventData &event);
    string         BuildEventJson(const VCPEventData &event);
    bool           SendHttpRequest(string json_body);
    bool           CacheToFile(const VCPEventData &events[], int count);
    bool           LoadFromCache();
    void           DebugLog(string message);
    
public:
    //--- Constructor/Destructor
    VCPLogger();
    ~VCPLogger();
    
    //--- Initialization
    bool           Initialize(const VCPConfig &config);
    void           Deinitialize();
    
    //--- ID Generation
    string         GenerateTraceID();
    
    //--- Timestamp
    long           GetCurrentTimestampMs();
    
    //--- Logging Methods
    bool           LogSIG(string trace_id, 
                          string algo_id, 
                          string gov_data_json = "");
    
    bool           LogORD(string trace_id, 
                          ulong ticket, 
                          ENUM_VCP_ORDER_SIDE side, 
                          string price, 
                          string volume,
                          ENUM_VCP_ORDER_TYPE order_type = VCP_TYPE_MARKET);
    
    bool           LogACK(string trace_id, 
                          ulong ticket, 
                          string broker_order_id = "");
    
    bool           LogEXE(string trace_id, 
                          ulong ticket, 
                          string exec_price, 
                          string exec_volume,
                          string commission = "0",
                          string slippage = "0");
    
    bool           LogPRT(string trace_id, 
                          ulong ticket, 
                          string exec_price, 
                          string exec_volume,
                          string remaining_volume);
    
    bool           LogREJ(string trace_id, 
                          ulong ticket, 
                          string reject_reason);
    
    bool           LogCXL(string trace_id, 
                          ulong ticket);
    
    bool           LogRSK(string trace_id, 
                          string risk_data_json);
    
    bool           LogERR(string trace_id, 
                          string error_code, 
                          string error_message);
    
    bool           LogHBT();
    
    bool           LogREC(string reason, 
                          int cached_count);
    
    //--- Queue Management
    bool           Enqueue(const VCPEventData &event);
    int            GetQueueSize();
    bool           Flush();
    
    //--- Timer Callback (call from OnTimer)
    void           OnTimerTick();
    
    //--- Configuration
    void           Configure(const VCPConfig &config);
    bool           IsInitialized();
    bool           IsConnected();
};
```

#### 6.3.3 Implementation Details

```cpp
//+------------------------------------------------------------------+
//|                     VCPLogger Implementation                      |
//+------------------------------------------------------------------+
VCPLogger::VCPLogger() {
    m_initialized = false;
    m_queue_head = 0;
    m_queue_tail = 0;
    m_queue_count = 0;
    m_prev_hash = StringInit(64, '0');  // 64 zeros for genesis
    m_last_send_time = 0;
}

VCPLogger::~VCPLogger() {
    Deinitialize();
}

bool VCPLogger::Initialize(const VCPConfig &config) {
    m_config = config;
    
    // Validate configuration
    if(m_config.api_key == "" || m_config.endpoint == "") {
        DebugLog("ERROR: API key and endpoint are required");
        return false;
    }
    
    // Initialize queue
    ArrayResize(m_queue, m_config.queue_size);
    
    // Load cached events if any
    if(m_config.enable_local_cache) {
        LoadFromCache();
    }
    
    m_initialized = true;
    DebugLog("VCPLogger initialized successfully");
    return true;
}

void VCPLogger::Deinitialize() {
    if(m_initialized) {
        Flush();
        m_initialized = false;
    }
}

string VCPLogger::GenerateTraceID() {
    return GenerateUuidV7();
}

string VCPLogger::GenerateUuidV7() {
    // UUID v7 implementation
    // Format: xxxxxxxx-xxxx-7xxx-yxxx-xxxxxxxxxxxx
    // Where x is random hex and y is 8, 9, a, or b
    
    long timestamp_ms = (long)(TimeCurrent()) * 1000 + GetTickCount() % 1000;
    
    string uuid = "";
    
    // Timestamp portion (48 bits = 12 hex chars)
    for(int i = 0; i < 12; i++) {
        int shift = (11 - i) * 4;
        int nibble = (int)((timestamp_ms >> shift) & 0xF);
        uuid += StringSubstr("0123456789abcdef", nibble, 1);
        
        if(i == 7) uuid += "-";
    }
    
    // Version (4 bits) = 7
    uuid += "-7";
    
    // Random (12 bits = 3 hex chars)
    for(int i = 0; i < 3; i++) {
        uuid += StringSubstr("0123456789abcdef", MathRand() % 16, 1);
    }
    
    uuid += "-";
    
    // Variant (2 bits = 10xx) + Random (14 bits)
    uuid += StringSubstr("89ab", MathRand() % 4, 1);
    for(int i = 0; i < 3; i++) {
        uuid += StringSubstr("0123456789abcdef", MathRand() % 16, 1);
    }
    
    uuid += "-";
    
    // Random (48 bits = 12 hex chars)
    for(int i = 0; i < 12; i++) {
        uuid += StringSubstr("0123456789abcdef", MathRand() % 16, 1);
    }
    
    return uuid;
}

string VCPLogger::GetCurrentTimestampInt() {
    // Return nanoseconds since epoch as string
    // MQL5 limitation: millisecond precision
    long ms = (long)(TimeCurrent()) * 1000 + GetTickCount() % 1000;
    return IntegerToString(ms) + "000000";  // Pad to nanoseconds
}

string VCPLogger::GetCurrentTimestampIso() {
    datetime now = TimeCurrent();
    int ms = GetTickCount() % 1000;
    
    return TimeToString(now, TIME_DATE|TIME_SECONDS) + 
           StringFormat(".%03dZ", ms);
}

bool VCPLogger::LogSIG(string trace_id, string algo_id, string gov_data_json) {
    if(!m_initialized) return false;
    
    VCPEventData event;
    event.event_id = GenerateUuidV7();
    event.trace_id = trace_id;
    event.timestamp_int = GetCurrentTimestampInt();
    event.timestamp_iso = GetCurrentTimestampIso();
    event.event_type_code = VCP_SIG;
    event.symbol = Symbol();
    event.account_id = IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
    event.algo_id = algo_id;
    event.gov_data_json = gov_data_json;
    
    return Enqueue(event);
}

bool VCPLogger::LogORD(string trace_id, ulong ticket, 
                        ENUM_VCP_ORDER_SIDE side, string price, 
                        string volume, ENUM_VCP_ORDER_TYPE order_type) {
    if(!m_initialized) return false;
    
    VCPEventData event;
    event.event_id = GenerateUuidV7();
    event.trace_id = trace_id;
    event.timestamp_int = GetCurrentTimestampInt();
    event.timestamp_iso = GetCurrentTimestampIso();
    event.event_type_code = VCP_ORD;
    event.symbol = Symbol();
    event.account_id = IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
    event.order_id = IntegerToString(ticket);
    event.side = (side == VCP_SIDE_BUY) ? "BUY" : "SELL";
    event.order_type = EnumToString(order_type);
    event.price = price;
    event.quantity = volume;
    
    return Enqueue(event);
}

bool VCPLogger::LogEXE(string trace_id, ulong ticket, 
                        string exec_price, string exec_volume,
                        string commission, string slippage) {
    if(!m_initialized) return false;
    
    VCPEventData event;
    event.event_id = GenerateUuidV7();
    event.trace_id = trace_id;
    event.timestamp_int = GetCurrentTimestampInt();
    event.timestamp_iso = GetCurrentTimestampIso();
    event.event_type_code = VCP_EXE;
    event.symbol = Symbol();
    event.account_id = IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
    event.order_id = IntegerToString(ticket);
    event.exec_price = exec_price;
    event.exec_qty = exec_volume;
    event.commission = commission;
    event.slippage = slippage;
    
    return Enqueue(event);
}

bool VCPLogger::LogERR(string trace_id, string error_code, string error_message) {
    if(!m_initialized) return false;
    
    VCPEventData event;
    event.event_id = GenerateUuidV7();
    event.trace_id = trace_id;
    event.timestamp_int = GetCurrentTimestampInt();
    event.timestamp_iso = GetCurrentTimestampIso();
    event.event_type_code = VCP_ERR;
    event.symbol = Symbol();
    event.account_id = IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
    event.error_code = error_code;
    event.error_message = error_message;
    
    return Enqueue(event);
}

bool VCPLogger::Enqueue(const VCPEventData &event) {
    if(m_queue_count >= m_config.queue_size) {
        DebugLog("WARNING: Queue full, dropping oldest event");
        m_queue_head = (m_queue_head + 1) % m_config.queue_size;
        m_queue_count--;
    }
    
    m_queue[m_queue_tail] = event;
    m_queue_tail = (m_queue_tail + 1) % m_config.queue_size;
    m_queue_count++;
    
    return true;
}

int VCPLogger::GetQueueSize() {
    return m_queue_count;
}

void VCPLogger::OnTimerTick() {
    if(!m_initialized) return;
    
    // Check if batch interval has passed
    if(GetTickCount() - m_last_send_time < m_config.batch_interval_ms) {
        return;
    }
    
    // Check if we have enough events for a batch
    if(m_queue_count >= m_config.batch_size || 
       (m_queue_count > 0 && GetTickCount() - m_last_send_time >= m_config.batch_interval_ms * 2)) {
        Flush();
    }
}

bool VCPLogger::Flush() {
    if(m_queue_count == 0) return true;
    
    // Build batch JSON
    string json_body = "[";
    int count = MathMin(m_queue_count, m_config.batch_size);
    
    for(int i = 0; i < count; i++) {
        int idx = (m_queue_head + i) % m_config.queue_size;
        if(i > 0) json_body += ",";
        json_body += BuildEventJson(m_queue[idx]);
    }
    json_body += "]";
    
    // Send request
    bool success = SendHttpRequest(json_body);
    
    if(success) {
        // Remove sent events from queue
        m_queue_head = (m_queue_head + count) % m_config.queue_size;
        m_queue_count -= count;
        m_last_send_time = GetTickCount();
        DebugLog(StringFormat("Sent %d events successfully", count));
    } else {
        // Cache to file if enabled
        if(m_config.enable_local_cache) {
            VCPEventData events_to_cache[];
            ArrayResize(events_to_cache, count);
            for(int i = 0; i < count; i++) {
                int idx = (m_queue_head + i) % m_config.queue_size;
                events_to_cache[i] = m_queue[idx];
            }
            CacheToFile(events_to_cache, count);
        }
    }
    
    return success;
}

string VCPLogger::BuildEventJson(const VCPEventData &event) {
    // Build canonical JSON representation
    string json = "{";
    
    // Header
    json += "\"header\":{";
    json += "\"event_id\":\"" + event.event_id + "\",";
    json += "\"trace_id\":\"" + event.trace_id + "\",";
    json += "\"timestamp_int\":\"" + event.timestamp_int + "\",";
    json += "\"timestamp_iso\":\"" + event.timestamp_iso + "\",";
    json += "\"event_type_code\":" + IntegerToString(event.event_type_code) + ",";
    json += "\"timestamp_precision\":\"MILLISECOND\",";
    json += "\"clock_sync_status\":\"" + EnumToString(m_config.clock_sync) + "\",";
    json += "\"hash_algo\":\"SHA256\",";
    json += "\"venue_id\":\"" + m_config.venue_id + "\",";
    json += "\"symbol\":\"" + event.symbol + "\",";
    json += "\"account_id\":\"" + event.account_id + "\"";
    json += "},";
    
    // Payload
    json += "\"payload\":{";
    
    if(event.event_type_code == VCP_SIG && event.gov_data_json != "") {
        json += "\"vcp_gov\":" + event.gov_data_json;
    } else if(event.event_type_code == VCP_ORD || 
              event.event_type_code == VCP_EXE ||
              event.event_type_code == VCP_ACK ||
              event.event_type_code == VCP_REJ) {
        json += "\"trade_data\":{";
        if(event.order_id != "") json += "\"order_id\":\"" + event.order_id + "\",";
        if(event.side != "") json += "\"side\":\"" + event.side + "\",";
        if(event.order_type != "") json += "\"order_type\":\"" + event.order_type + "\",";
        if(event.price != "") json += "\"price\":\"" + event.price + "\",";
        if(event.quantity != "") json += "\"quantity\":\"" + event.quantity + "\",";
        if(event.exec_price != "") json += "\"execution_price\":\"" + event.exec_price + "\",";
        if(event.exec_qty != "") json += "\"executed_qty\":\"" + event.exec_qty + "\",";
        if(event.commission != "") json += "\"commission\":\"" + event.commission + "\",";
        if(event.slippage != "") json += "\"slippage\":\"" + event.slippage + "\",";
        if(event.reject_reason != "") json += "\"reject_reason\":\"" + event.reject_reason + "\",";
        // Remove trailing comma
        json = StringSubstr(json, 0, StringLen(json) - 1);
        json += "}";
    } else if(event.event_type_code == VCP_ERR) {
        json += "\"error\":{";
        json += "\"code\":\"" + event.error_code + "\",";
        json += "\"message\":\"" + event.error_message + "\"";
        json += "}";
    } else if(event.event_type_code == VCP_RSK && event.risk_data_json != "") {
        json += "\"vcp_risk\":" + event.risk_data_json;
    }
    
    json += "},";
    
    // Security (simplified - VCC will compute full hash chain)
    json += "\"security\":{";
    json += "\"prev_hash\":\"" + m_prev_hash + "\"";
    json += "}";
    
    json += "}";
    
    return json;
}

bool VCPLogger::SendHttpRequest(string json_body) {
    char post_data[];
    StringToCharArray(json_body, post_data, 0, WHOLE_ARRAY, CP_UTF8);
    
    char result[];
    string headers = "Content-Type: application/json\r\n";
    headers += "Authorization: Bearer " + m_config.api_key + "\r\n";
    
    string result_headers;
    
    int timeout = 5000;  // 5 seconds
    
    int res = WebRequest(
        "POST",
        m_config.endpoint + "/events/batch",
        headers,
        timeout,
        post_data,
        result,
        result_headers
    );
    
    if(res == -1) {
        int error = GetLastError();
        DebugLog(StringFormat("WebRequest error: %d", error));
        return false;
    }
    
    if(res >= 200 && res < 300) {
        return true;
    }
    
    DebugLog(StringFormat("HTTP error: %d", res));
    return false;
}

void VCPLogger::DebugLog(string message) {
    if(m_config.debug) {
        Print("[VCP] " + message);
    }
}
```

### 6.4 Configuration

```cpp
//+------------------------------------------------------------------+
//|                    Default Configuration                          |
//+------------------------------------------------------------------+
VCPConfig GetDefaultConfig() {
    VCPConfig config;
    
    config.api_key = "";  // Required
    config.endpoint = "https://api.veritaschain.org/v1";
    config.venue_id = "MT5-DEFAULT";
    config.async_mode = true;
    config.queue_size = 1000;
    config.batch_size = 50;
    config.batch_interval_ms = 1000;
    config.retry_count = 3;
    config.retry_delay_ms = 1000;
    config.enable_local_cache = true;
    config.cache_file_path = "VCP_cache.json";
    config.debug = false;
    config.clock_sync = VCP_CLOCK_BEST_EFFORT;
    
    return config;
}
```

### 6.5 Usage Patterns

#### 6.5.1 Basic EA Integration

```cpp
//+------------------------------------------------------------------+
//|                                              MyTradingEA.mq5      |
//+------------------------------------------------------------------+
#include <VCP/VCPLogger.mqh>

// Global logger instance
VCPLogger g_vcpLogger;

// Input parameters
input string InpVcpApiKey = "";  // VCP API Key
input string InpVcpEndpoint = "https://api.veritaschain.org/v1";  // VCP Endpoint
input string InpVcpVenueId = "MT5-MYBROKER";  // Venue ID
input bool   InpVcpDebug = false;  // Debug Mode

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit() {
    // Configure VCP Logger
    VCPConfig config = GetDefaultConfig();
    config.api_key = InpVcpApiKey;
    config.endpoint = InpVcpEndpoint;
    config.venue_id = InpVcpVenueId;
    config.debug = InpVcpDebug;
    
    if(!g_vcpLogger.Initialize(config)) {
        Print("Failed to initialize VCP Logger");
        return INIT_FAILED;
    }
    
    // Set timer for background sending
    EventSetMillisecondTimer(100);
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
    EventKillTimer();
    g_vcpLogger.Deinitialize();
}

//+------------------------------------------------------------------+
//| Timer function                                                    |
//+------------------------------------------------------------------+
void OnTimer() {
    g_vcpLogger.OnTimerTick();
}

//+------------------------------------------------------------------+
//| Trade function                                                    |
//+------------------------------------------------------------------+
void OnTrade() {
    // Called when trade events occur
    // Implementation for trade event detection
}

//+------------------------------------------------------------------+
//| Example: Signal Generation and Order Execution                   |
//+------------------------------------------------------------------+
void ExecuteTradeSignal(double signal_strength) {
    // Generate trace ID for this trade lifecycle
    string trace_id = g_vcpLogger.GenerateTraceID();
    
    // 1. Log Signal Event with VCP-GOV
    string gov_json = StringFormat(
        "{\"algo_id\":\"my-strategy-v1\",\"algo_version\":\"1.0.0\",\"decision_factors\":{\"confidence_score\":\"%s\"}}",
        DoubleToString(signal_strength, 4)
    );
    g_vcpLogger.LogSIG(trace_id, "my-strategy-v1", gov_json);
    
    // 2. Execute order
    double price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double volume = 0.1;
    
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = _Symbol;
    request.volume = volume;
    request.type = ORDER_TYPE_BUY;
    request.price = price;
    request.deviation = 10;
    request.magic = 12345;
    
    // Log Order Event before sending
    g_vcpLogger.LogORD(
        trace_id,
        0,  // ticket will be assigned
        VCP_SIDE_BUY,
        DoubleToString(price, _Digits),
        DoubleToString(volume, 2)
    );
    
    // Send order
    if(OrderSend(request, result)) {
        if(result.retcode == TRADE_RETCODE_DONE) {
            // 3. Log Execution Event
            g_vcpLogger.LogEXE(
                trace_id,
                result.order,
                DoubleToString(result.price, _Digits),
                DoubleToString(result.volume, 2),
                "0",  // Commission (query later)
                DoubleToString(result.price - price, _Digits)  // Slippage
            );
        } else {
            // Log Rejection Event
            g_vcpLogger.LogREJ(
                trace_id,
                result.order,
                IntegerToString(result.retcode)
            );
        }
    } else {
        // Log Error Event
        g_vcpLogger.LogERR(
            trace_id,
            IntegerToString(GetLastError()),
            "OrderSend failed"
        );
    }
}
```

### 6.6 DLL Integration

For advanced use cases requiring true asynchronous HTTP operations, a C++ DLL can be used:

```cpp
// VCPBridge.dll exports
extern "C" {
    __declspec(dllexport) bool __stdcall VCP_Initialize(
        const char* api_key, 
        const char* endpoint
    );
    
    __declspec(dllexport) void __stdcall VCP_Deinitialize();
    
    __declspec(dllexport) bool __stdcall VCP_EnqueueEvent(
        const char* json_event
    );
    
    __declspec(dllexport) int __stdcall VCP_GetQueueSize();
    
    __declspec(dllexport) bool __stdcall VCP_Flush();
    
    __declspec(dllexport) bool __stdcall VCP_IsConnected();
}
```

**MQL5 Import:**

```cpp
#import "VCPBridge.dll"
    bool VCP_Initialize(string api_key, string endpoint);
    void VCP_Deinitialize();
    bool VCP_EnqueueEvent(string json_event);
    int  VCP_GetQueueSize();
    bool VCP_Flush();
    bool VCP_IsConnected();
#import
```

---

## 7. Error Handling

### 7.1 Error Categories

| Category | Description | SDK Behavior |
|----------|-------------|--------------|
| **Network** | Connection failures, timeouts | Auto-retry + queue |
| **Serialization** | Invalid data types, encoding | Immediate exception |
| **Authentication** | Invalid API key | Immediate exception |
| **Validation** | Schema violations | Immediate exception |
| **Server** | VCC internal errors | Auto-retry |
| **Rate Limit** | Too many requests | Exponential backoff |

### 7.2 Error Codes

| Code | Name | Description | Recovery |
|------|------|-------------|----------|
| `VCP_E001` | NETWORK_ERROR | Network connectivity issue | Retry |
| `VCP_E002` | TIMEOUT | Request timeout | Retry |
| `VCP_E003` | AUTH_FAILED | Invalid API key | None |
| `VCP_E004` | INVALID_EVENT | Event validation failed | Fix data |
| `VCP_E005` | NUMERIC_TYPE | Number used instead of string | Fix data |
| `VCP_E006` | INVALID_UUID | Invalid UUID format | Fix data |
| `VCP_E007` | SERVER_ERROR | VCC server error | Retry |
| `VCP_E008` | RATE_LIMITED | Rate limit exceeded | Backoff |
| `VCP_E009` | QUEUE_FULL | Local queue full | Flush |
| `VCP_E010` | NOT_INITIALIZED | Logger not initialized | Initialize |

### 7.3 Retry Policy

**Default Configuration:**

```
max_retries: 3
initial_delay_ms: 1000
max_delay_ms: 30000
backoff_multiplier: 2.0
jitter: true (±10%)
```

**Retry Decision Matrix:**

| HTTP Status | Retry | Notes |
|-------------|-------|-------|
| 2xx | No | Success |
| 400 | No | Bad request - fix data |
| 401 | No | Authentication failure |
| 403 | No | Forbidden |
| 404 | No | Not found |
| 408 | Yes | Request timeout |
| 429 | Yes | Rate limited (use Retry-After) |
| 5xx | Yes | Server error |
| Network Error | Yes | Connection issue |

### 7.4 Offline Mode

When network connectivity is unavailable:

1. Events are queued in memory (up to `queue_size`)
2. If `enable_local_cache` is true, overflow events are written to disk
3. When connectivity is restored:
   - Cached events are loaded
   - A `VCP_REC` (Recovery) event is generated
   - Events are sent in chronological order

**Cache File Format:**

```json
{
  "version": "1.0",
  "created_at": "2025-11-25T12:00:00Z",
  "events": [
    { /* VcpEvent */ },
    { /* VcpEvent */ }
  ]
}
```

---

## 8. Security Considerations

### 8.1 API Key Management

**Requirements:**

- API keys MUST NOT be hardcoded in source code
- API keys MUST be stored securely (environment variables, secrets manager)
- API keys MUST be transmitted only over HTTPS
- API keys SHOULD be rotated periodically

**Implementation Examples:**

```typescript
// TypeScript - Environment variable
const logger = createLogger({
  endpoint: process.env.VCP_ENDPOINT!,
  apiKey: process.env.VCP_API_KEY!
});

# Python - Environment variable
import os
logger = create_logger(VcpLoggerConfig(
    endpoint=os.environ["VCP_ENDPOINT"],
    api_key=os.environ["VCP_API_KEY"]
))
```

### 8.2 Transport Security

**Requirements:**

- All communication MUST use HTTPS (TLS 1.2 or higher)
- SDKs MUST verify server certificates
- SDKs SHOULD support certificate pinning (optional)

### 8.3 Data Privacy

**Account ID Pseudonymization:**

SDKs MUST provide utilities for pseudonymizing account IDs:

```typescript
// Do NOT use raw account IDs
const badId = "123456789";  // Real account number

// DO use pseudonymized IDs
const goodId = pseudonymizeAccountId("123456789", "my-salt");
// Result: "acc_7f83b162f9..." (SHA-256 truncated)
```

**Sensitive Data Handling:**

- Passwords, PINs, and authentication tokens MUST NOT be logged
- Personal Identifiable Information (PII) SHOULD be pseudonymized
- SDKs SHOULD support VCP-PRIVACY module for data retention policies

---

## 9. Testing and Validation

### 9.1 Unit Testing

SDKs MUST include unit tests for:

- UUID v7 generation (format and uniqueness)
- Timestamp generation (both formats)
- JSON canonicalization (RFC 8785 compliance)
- Event hash calculation
- Numeric to string conversion

**Example Test Cases:**

```typescript
// TypeScript (Jest)
describe('generateUuidV7', () => {
  it('should generate valid UUID v7 format', () => {
    const uuid = generateUuidV7();
    expect(uuid).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
    );
  });
  
  it('should be time-ordered', () => {
    const uuid1 = generateUuidV7();
    const uuid2 = generateUuidV7();
    expect(uuid2 > uuid1).toBe(true);
  });
});

describe('canonicalizeJson', () => {
  it('should sort keys lexicographically', () => {
    const result = canonicalizeJson({ b: 2, a: 1 });
    expect(result).toBe('{"a":1,"b":2}');
  });
  
  it('should handle nested objects', () => {
    const result = canonicalizeJson({ b: { d: 4, c: 3 }, a: 1 });
    expect(result).toBe('{"a":1,"b":{"c":3,"d":4}}');
  });
});
```

### 9.2 Integration Testing

SDKs SHOULD include integration tests against VCC sandbox:

```typescript
describe('Logger Integration', () => {
  it('should send event to VCC', async () => {
    const logger = createLogger({
      endpoint: 'https://sandbox.veritaschain.org/v1',
      apiKey: process.env.VCP_SANDBOX_KEY!
    });
    
    const event = createTestEvent('SIG');
    await logger.log(event);
    await logger.flush();
    
    // Verify via Explorer
    const explorer = createExplorer({
      endpoint: 'https://sandbox.veritaschain.org/v1',
      apiKey: process.env.VCP_SANDBOX_KEY!
    });
    
    const retrieved = await explorer.getEventById(event.header.event_id);
    expect(retrieved).not.toBeNull();
    expect(retrieved!.header.event_id).toBe(event.header.event_id);
  });
});
```

### 9.3 Conformance Testing

See **VCP Conformance Test Guide** (VSO-TEST-001) for:

- Schema validation tests
- Hash chain verification tests
- Merkle proof verification tests
- Tier-specific requirement tests

---

## 10. Versioning

### 10.1 Version Scheme

SDK versions follow Semantic Versioning 2.0.0:

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (API incompatible)
MINOR: New features (backward compatible)
PATCH: Bug fixes (backward compatible)
```

**SDK-to-Protocol Version Alignment:**

- SDK major version MUST match VCP Specification major version
- SDK 1.x.x implements VCP Specification 1.0

### 10.2 Compatibility Matrix

| SDK Version | VCP Spec | VCC API | Min Runtime |
|-------------|----------|---------|-------------|
| 1.0.x | 1.0 | v1 | Node 18+ / Python 3.10+ / MT5 Build 3000+ |
| 1.1.x | 1.0 | v1, v1.1 | Node 18+ / Python 3.10+ / MT5 Build 3000+ |

**Internal Version Field:**

SDKs MUST expose a version constant:

```typescript
// TypeScript
export const VCP_SDK_VERSION = '1.0.0';
export const VCP_SPEC_VERSION = '1.0';

# Python
VCP_SDK_VERSION = '1.0.0'
VCP_SPEC_VERSION = '1.0'

// MQL5
#define VCP_SDK_VERSION "1.0.0"
#define VCP_SPEC_VERSION "1.0"
```

---

## 11. Appendices

### Appendix A: Complete Type Definitions

See individual language sections for complete type definitions.

### Appendix B: JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "VCP Event Schema v1.0",
  "type": "object",
  "required": ["header", "payload", "security"],
  "properties": {
    "header": {
      "type": "object",
      "required": [
        "event_id", "trace_id", "timestamp_int", "timestamp_iso",
        "event_type", "event_type_code", "timestamp_precision",
        "clock_sync_status", "hash_algo", "venue_id", "symbol", "account_id"
      ],
      "properties": {
        "event_id": {
          "type": "string",
          "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        },
        "trace_id": {
          "type": "string",
          "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        },
        "timestamp_int": { "type": "string", "pattern": "^[0-9]+$" },
        "timestamp_iso": { "type": "string", "format": "date-time" },
        "event_type": {
          "type": "string",
          "enum": ["SIG","ORD","ACK","EXE","PRT","REJ","CXL","MOD","CLS","ALG","RSK","AUD","HBT","ERR","REC","SNC"]
        },
        "event_type_code": { "type": "integer", "minimum": 1, "maximum": 255 },
        "timestamp_precision": {
          "type": "string",
          "enum": ["NANOSECOND", "MICROSECOND", "MILLISECOND"]
        },
        "clock_sync_status": {
          "type": "string",
          "enum": ["PTP_LOCKED", "NTP_SYNCED", "BEST_EFFORT", "UNRELIABLE"]
        },
        "hash_algo": {
          "type": "string",
          "enum": ["SHA256", "SHA3_256", "BLAKE3"]
        },
        "venue_id": { "type": "string" },
        "symbol": { "type": "string" },
        "account_id": { "type": "string" },
        "operator_id": { "type": ["string", "null"] }
      }
    },
    "payload": {
      "type": "object",
      "properties": {
        "trade_data": { "$ref": "#/definitions/VcpTradePayload" },
        "vcp_risk": { "$ref": "#/definitions/VcpRiskPayload" },
        "vcp_gov": { "$ref": "#/definitions/VcpGovPayload" },
        "vcp_privacy": { "type": "object" },
        "vcp_recovery": { "type": "object" }
      }
    },
    "security": {
      "type": "object",
      "required": ["event_hash", "prev_hash"],
      "properties": {
        "event_hash": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
        "prev_hash": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
        "signature": { "type": "string" },
        "sign_algo": {
          "type": "string",
          "enum": ["ED25519", "ECDSA_SECP256K1", "RSA_2048", "DILITHIUM2", "FALCON512"]
        },
        "merkle_root": { "type": "string" },
        "anchor": {
          "type": "object",
          "properties": {
            "network": { "type": "string" },
            "tx_hash": { "type": "string" },
            "block_number": { "type": "integer" },
            "anchored_at": { "type": "string", "format": "date-time" }
          }
        }
      }
    }
  },
  "definitions": {
    "VcpTradePayload": {
      "type": "object",
      "properties": {
        "order_id": { "type": "string" },
        "broker_order_id": { "type": "string" },
        "exchange_order_id": { "type": "string" },
        "side": { "type": "string", "enum": ["BUY", "SELL"] },
        "order_type": { "type": "string", "enum": ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"] },
        "price": { "type": "string" },
        "quantity": { "type": "string" },
        "executed_qty": { "type": "string" },
        "remaining_qty": { "type": "string" },
        "currency": { "type": "string" },
        "execution_price": { "type": "string" },
        "commission": { "type": "string" },
        "slippage": { "type": "string" },
        "reject_reason": { "type": "string" }
      }
    },
    "VcpRiskPayload": {
      "type": "object",
      "properties": {
        "snapshot": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        },
        "triggered_controls": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["control_name", "trigger_value", "action", "timestamp_int"],
            "properties": {
              "control_name": { "type": "string" },
              "trigger_value": { "type": "string" },
              "action": { "type": "string" },
              "timestamp_int": { "type": "string" }
            }
          }
        }
      }
    },
    "VcpGovPayload": {
      "type": "object",
      "properties": {
        "algo_id": { "type": "string" },
        "algo_version": { "type": "string" },
        "algo_type": { "type": "string", "enum": ["AI_MODEL", "RULE_BASED", "HYBRID"] },
        "model_hash": { "type": "string" },
        "risk_classification": { "type": "string", "enum": ["HIGH", "MEDIUM", "LOW"] },
        "last_approval_by": { "type": "string" },
        "approval_timestamp_int": { "type": "string" },
        "testing_record_link": { "type": "string" },
        "decision_factors": {
          "type": "object",
          "properties": {
            "features": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["name", "value"],
                "properties": {
                  "name": { "type": "string" },
                  "value": { "type": "string" },
                  "weight": { "type": "string" },
                  "contribution": { "type": "string" }
                }
              }
            },
            "confidence_score": { "type": "string" },
            "explainability_method": {
              "type": "string",
              "enum": ["SHAP", "LIME", "GRADCAM", "RULE_TRACE"]
            }
          }
        }
      }
    }
  }
}
```

### Appendix C: Implementation Checklist

#### Pre-Release Checklist

- [ ] All core types implemented
- [ ] Logger client with queue and batch support
- [ ] Explorer client with all endpoints
- [ ] UUID v7 generation
- [ ] Dual timestamp format
- [ ] RFC 8785 JSON canonicalization
- [ ] Event hash calculation
- [ ] Numeric-to-string utilities
- [ ] Account ID pseudonymization
- [ ] Error handling with categories
- [ ] Retry policy implementation
- [ ] Local cache support
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests with sandbox
- [ ] API documentation
- [ ] Usage examples

#### Tier Compatibility Checklist

**Silver Tier:**
- [ ] JSON serialization
- [ ] Delegated signature support
- [ ] MILLISECOND timestamp precision
- [ ] BEST_EFFORT clock sync support
- [ ] Local cache for offline mode

**Gold Tier:**
- [ ] Self-signing (Ed25519)
- [ ] MICROSECOND timestamp precision
- [ ] NTP_SYNCED clock sync
- [ ] WebSocket support (optional)

**Platinum Tier:**
- [ ] SBE binary format (optional)
- [ ] NANOSECOND timestamp precision
- [ ] PTP_LOCKED clock sync
- [ ] HSM integration (optional)

### Appendix D: Reference Documents

| Document | ID | Description |
|----------|-----|-------------|
| VCP Specification v1.0 | VSO-SPEC-001 | Core protocol specification |
| VCP API Reference v1.1 | VSO-API-001 | VCC API documentation |
| VCP Sidecar Integration Guide | VSO-INTEG-001 | Integration patterns |
| VCP Conformance Test Guide | VSO-TEST-001 | Certification testing |
| VC-Certified Program Guide | VSO-CERT-001 | Certification requirements |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-25 | VSO | Initial release |

---

*Copyright © 2025 VeritasChain Standards Organization. Licensed under Apache 2.0.*
