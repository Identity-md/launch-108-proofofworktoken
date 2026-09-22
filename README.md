# Proof Of Work (WORK)

`ProofOfWorkToken` is the sole launch contract in this project: an ERC-20 named **Proof Of Work**, symbol **WORK**, with 18 decimals. Its nonpayable, argument-free constructor mints exactly `1000000000000000000000000000` minor units (one billion WORK) to its immediate caller. During launch that caller must be the configured ProjectFactory.

The implementation extends the vendored OpenZeppelin Contracts v5.0.2 ERC20 without overriding transfer or allowance behavior. It has no owner, external mint/burn function, initializer, upgrade mechanism, transfer tax, blacklist, pause control, or token recovery function. The entire supply exists at construction; subsequent transfers preserve it. Internal library mint/burn routines are not public entry points.

## Offline build and tests

Prerequisites are Foundry (`forge` and `cast`) and the standard Solidity **0.8.26** compiler already installed in Foundry's compiler cache. Validation used Foundry 1.7.1. Python 3.9+ is needed only for the ABI export utility. No dependency installation, RPC, wallet, fork, environment file, or package manager is required.

```sh
forge build
forge test
forge fmt --check
python3 scripts/export_abis.py --check
```

`foundry.toml` enables offline mode and pins Solidity 0.8.26, Cancun, optimizer 200 runs, `via_ir = false`, `bytecode_hash = "none"`, and no CBOR trailer. FFI and cheatcode filesystem access are disabled. Source dependencies and forge-std v1.9.7 are ordinary files under `lib/`, with licenses, upstream versions, archive hashes, and file hashes recorded in [docs/dependencies.json](docs/dependencies.json). There are no submodules or network-dependent tests.

The tests exercise immediate factory ownership of the initial supply through CREATE2, exact metadata and mint event, complete and partial transfers, zero/self transfers, approval replacement/revocation, allowance isolation, finite and infinite allowance spending, failure rollback, invalid addresses, insufficient funds/allowance, rejected admin selectors, nonpayability, and runtime opcode/size constraints. Fuzz tests cover arbitrary deployment callers and transfer amounts; a stateful handler checks supply, balances, and allowance accounting across sequences of real token calls. Helpers in `test/` exist only inside the local test EVM.

## Integration handoff

- [Launch parameters and responsibilities](docs/launch-handoff.md): token-only manifest requirements and policy/service boundary.
- [Protocol claim integration](docs/integration.md): actual distributor ABI, Merkle format, verification gates, and sweep limitations.
- [Token ABI](docs/abi/ProofOfWorkToken.json) and [protocol distributor ABI](docs/abi/MerkleDistributor.json): raw compiler-derived JSON arrays.
- [ABI hashes](docs/abi-hashes.json): canonical Keccak-256 and exact-file SHA-256, lowercase without `0x`.
- [Local validation](docs/validation.md): test results, protected-check setup, and verification limits.

Regenerate exports with `python3 scripts/export_abis.py`. The distributor's exact upstream source and dependency closure are preserved as documentation data in [docs/protocol/MerkleDistributor.sources.json](docs/protocol/MerkleDistributor.sources.json); the export tool compiles them in a temporary directory without deploying anything. They are not application contracts in this project.

This contribution implements the token and prepares integration documentation. The separate manifest assignment writes `launch.json` with `kind: "evm_project"` and `contracts: []`; an independent contributor reviews accepted source and that manifest. Services subsequently publish, attest, admit, and deploy. The later frontend assignment consumes the verified deployment. No launch address, allocation snapshot, claim proof, signed artifact, frontend, or transaction is fabricated here. Test results are local evidence, not an independent security audit.
