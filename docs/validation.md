# Local validation

Validation used Forge 1.7.1 (`4072e48705af9d93e3c0f6e29e93b5e9a40caed8`) and the installed native Solidity 0.8.26 compiler. All compilation and tests ran with Foundry offline mode enabled. No fork, RPC, wallet signing, or broadcast was used.

| Check | Result |
| --- | --- |
| `forge build` | Passed with the pinned configuration |
| `forge test` | 32 passed, 0 failed, 0 skipped |
| Fuzz tests | 4 properties, 256 cases each |
| Stateful invariant | 128 sequences of depth 64: 8,192 calls, 0 reverts |
| `forge fmt --check` | Passed |
| `python3 scripts/export_abis.py --check` | Both ABI exports and their hashes reproduced offline |
| Supplied `Token.protected.t.sol` | 6 passed, 0 failed, 0 skipped |
| Supplied `Project.protected.t.sol` | 2 passed, 0 failed, 0 skipped |
| Isolated offline source rebuild in a fresh directory | Creation bytecode, runtime bytecode, and ABI matched exactly |
| Vendored dependencies | Every file matched its recorded SHA-256 |
| Token ABI | Export matched the compiler artifact ABI exactly |

The protected suites were copied unchanged into temporary `test/scratch/` files, run with the actual compiled token creation code, 18 decimals, expected supply `10^27`, Sepolia chain ID, a local test factory, and zero application contracts. The protected CREATE2 address was computed from that test factory, salt, and creation code. No live factory address was assumed. The application runtime loop is empty for this intentionally token-only launch; the protected token runtime scan and the project's own runtime test actually inspected token bytecode. The temporary protected test copies were removed after execution so default tests require no environment variables.

Token creation code is 2,599 bytes and deployed runtime is 1,709 bytes under the pinned settings. Runtime inspection excludes PUSH data and found no DELEGATECALL, CALLCODE, or SELFDESTRUCT. The token remains well below the EIP-170 runtime size limit.

The initial local test run exposed an incorrect test expectation for a zero sender in `transferFrom`: OpenZeppelin validates the approver while spending allowance before validating the transfer sender. The assertion was corrected to `ERC20InvalidApprover(address(0))`; the complete suite subsequently passed. No token implementation change was required.

These results cover the delivered token and reproducibility of ABI documentation. They are not an independent review, a protocol distributor audit, live deployment verification, a signed attestation, or frontend/browser evidence. The separate reviewer must inspect accepted source and `launch.json`; services and the future frontend must verify actual deployment, allocation funding, ABI handoff binding, and the documented protocol sweep limitations.
