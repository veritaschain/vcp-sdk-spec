<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <title>VeritasChain Protocol SDK Specification v1.0</title>
</head>
<body>
  <h1>VeritasChain Protocol SDK Specification v1.0</h1>

  <p>
    This repository defines the Software Development Kit specification for
    VeritasChain Protocol VCP.
    It describes common data models, logging clients, and explorer clients
    for implementations in TypeScript, Python, and MQL5 bridge environments.
  </p>

  <h2>Scope</h2>
  <ul>
    <li>Unified VCP event model header, payload, security for all client SDKs</li>
    <li>Requirements for UUID v7 identifiers, time handling, and numeric as string rules</li>
    <li>Language level interfaces for logging to VeritasChain Cloud VCC</li>
    <li>Language level clients for the VCP Explorer API search, proof, certificate</li>
    <li>Guidance for Silver, Gold, and Platinum tier compatible SDKs</li>
  </ul>

  <h2>Main document</h2>
  <p>
    The full textual specification is provided in the following file.
  </p>
  <ul>
    <li>
      <strong>VCP SDK Specification v1.0 English</strong><br>
      <code>VCP_SDK_SPECIFICATION_v1_0_EN.md</code>
    </li>
  </ul>

  <h2>Target languages</h2>
  <ul>
    <li>TypeScript  Node and browser compatible</li>
    <li>Python  server side services and batch tools</li>
    <li>MQL5 bridge  MT5 expert advisors and sidecar logging</li>
  </ul>

  <h2>Relation to other VCP repositories</h2>
  <p>
    This repository focuses on the abstract SDK contract.
    Concrete implementations and other components are expected to live in separate repositories,
    for example:
  </p>
  <ul>
    <li>vcp spec  core VeritasChain Protocol specification</li>
    <li>vcp explorer api  Explorer service and API reference</li>
    <li>vcp sidecar guide  Silver tier sidecar integration guide for MT4 MT5 and white label platforms</li>
    <li>vcp market intelligence  industry research supporting VCP adoption</li>
  </ul>

  <h2>Intended audience</h2>
  <ul>
    <li>SDK maintainers and client library authors</li>
    <li>Exchange and broker engineering teams integrating VCP</li>
    <li>Prop firm and platform vendors building sidecar or gateway services</li>
    <li>Conformance and certification engineers preparing VC Certified test suites</li>
  </ul>

  <p>
    All changes to this specification should be proposed through issues and pull requests
    so that implementations in all supported languages stay aligned with the VeritasChain
    Protocol VCP v1 series.
  </p>
</body>
</html>
