# Protocol MerkleDistributor integration

## ABI provenance and exact interface

[abi/MerkleDistributor.json](abi/MerkleDistributor.json) is the full compiler-derived ABI of `packages/contracts/src/MerkleDistributor.sol` in `surfer77/IMD2` at commit `a94632d6ea40fbd2d1bcd8a0aafe53a1619956c6`. The pinned source was read from the local platform checkout because the public GitHub URL returned 404. Its exact source and all 10 imported source files are preserved in [protocol/MerkleDistributor.sources.json](protocol/MerkleDistributor.sources.json), with SHA-256 digests and upstream paths. Its OpenZeppelin dependencies are those from that platform commit, distinct from the token's v5.0.2 dependency. The export script recompiles this data offline with Solidity 0.8.26. It never deploys a distributor.

The claim entry point is:

```solidity
function claim(uint256 round, address account, uint256 amount, bytes32[] calldata proof) external;
```

It is **nonpayable**, returns nothing, and pays the `account` in the proven leaf. Any caller may submit a valid claim; the website must use only `claim(0, connectedWallet, allocationAmount, proof)` with zero ETH value. It must never ask the wallet to approve or transfer tokens. The user still needs Sepolia ETH for transaction gas.

Read functions used by integration:

| Signature | Return value |
| --- | --- |
| `token()` | `address` |
| `roundCount()` | `uint256` |
| `roundOf(uint256 round)` | One tuple: `(bytes32 root, uint256 funded, uint256 claimed, uint64 unlocksAt)` |
| `claimed(uint256 round, address account)` | `bool` |
| `openedAt(uint256 round)` | `uint64` |
| `owner()` | `address` |
| `treasury()` | `address` |
| `sweepDelay()` | `uint64` |

`roundOf(0).claimed` is the cumulative amount, whereas `claimed(0, wallet)` is a per-wallet boolean. There is **no `swept` field or getter**, no bitmap leaf index, and no claim deadline getter. A missing round reverts `NoSuchRound()`.

Events are `RoundOpened(uint256 indexed round, bytes32 root, uint256 funded, uint64 unlocksAt)`, `Claimed(uint256 indexed round, address indexed account, uint256 amount)`, and `Swept(address indexed to, uint256 amount)`. `Swept` contains no round identifier. Claim errors include `NoSuchRound()`, `StillLocked(uint64 unlocksAt)`, `AlreadyClaimed()`, and `InvalidProof()`. Transfer failure can bubble token errors or `SafeERC20FailedOperation(address token)`; a failed transfer reverts the claimed flag and accounting changes as well.

The full ABI includes protocol constructor and owner operations for inspection, not website controls. Only services supply `token_`, `owner_`, `treasury_`, and `sweepDelay_` and operate `openRound`, `sweep`, or `transferOwnership` as authorized. ABI completeness is not authorization to invoke those functions.

## Allocation format

Use OpenZeppelin [StandardMerkleTree](https://github.com/OpenZeppelin/merkle-tree) with leaf types **`["address", "uint256"]`**, default sorted leaves, and sorted sibling pairs. The leaf is:

```solidity
keccak256(bytes.concat(keccak256(abi.encode(account, amount))))
```

Internal nodes hash the two `bytes32` values in ascending order. The round, chain ID, distributor address, and leaf index are not part of the leaf. Select the correct deployment and round separately. Keep all amounts as exact decimal minor-unit strings in JSON and `bigint` in application code; never use JavaScript `Number`, floating point, display units, or packed ABI encoding to construct leaves.

After services freeze the allocations, the frontend contribution must:

1. Save **every** wallet/amount row from the actual allocation snapshot. Validate addresses, exact unsigned decimal amounts, uint256 bounds, and uniqueness by normalized wallet address. Reject duplicate wallets or malformed data; ask services to repair the snapshot rather than inventing a merged allocation. The service is responsible for combining the approved 2%/8% overlap beforehand.
2. Build `StandardMerkleTree.of(rows, ["address", "uint256"])` with all rows. A wallet-only subset cannot reproduce the launch root. Compare the rebuilt root to both `launch.merkleRoot` and `roundOf(0).root`.
3. Generate each proof using that row's tree entry index, verify it locally, and save the tree dump plus a static `claims.json` containing the actual chain, token, distributor, round `0`, root, snapshot provenance, and per-wallet decimal `amount` and `bytes32[] proof`. An entry index is used off chain only. An empty proof can be valid for a single-leaf tree; it is not evidence of ineligibility.
4. Check the snapshot's sum against round funding and the frozen service allocation. Do not recalculate policy, invent recipients, or silently correct mismatches. There is no real snapshot or proof available at the contract implementation stage.

For later frontend code, the essential operations are `StandardMerkleTree.of(rows, ["address", "uint256"])`, `tree.entries()`, `tree.getProof(entryIndex)`, and `StandardMerkleTree.verify(root, ["address", "uint256"], [wallet, amountString], proof)`. The frontend assignment must pin its own JS dependencies and test malformed, duplicate, absent, and tampered allocations.

## Required verification before enabling Claim

Load the actual `.imd/reads/deployment.json` handoff in the frontend assignment. Discover the distributor using `GET https://api.imd.fun/launches/<handoff launchId>` and its artifact with role `distributor`. Do not infer an address from a token name or deploy a helper. Validate handoff identifiers, source, chain and ABI binding before creating runtime configuration.

Perform successful RPC reads on Sepolia and use a consistent block for related state where possible:

1. Verify RPC chain ID `11155111` and nonempty deployed code at both token and distributor. Verify the connected wallet is on Sepolia, offering a chain switch otherwise.
2. Check distributor `token()` equals the handoff token. Check round 0 exists and the rebuilt snapshot root, launch root, and on-chain root all agree. Compare `funded` to the snapshot sum and require coherent `claimed <= funded` accounting.
3. Read token `balanceOf(connectedWallet)`, `claimed(0, connectedWallet)`, and round `unlocksAt`. Derive unlock from the current chain block timestamp. At the exact unlock timestamp, claims are permitted. A browser clock may show a countdown but cannot authorize a claim.
4. Read WORK `balanceOf(distributor)`, `openedAt(0)`, `sweepDelay()`, and relevant confirmed `Swept` logs from the actual deployment block. Use `max(openedAt(0) + sweepDelay(), unlocksAt)` as the earliest round-0 sweep time, not an automatic claim expiry. Keep Claim disabled if funding is insufficient, required logs/reads fail, or sweep/funding status is unresolved. A positive sweep event with unresolved later funding should show a swept/unavailable state, not claimable rewards.
5. Require the wallet's snapshot entry and valid proof, `claimed(0,wallet) == false`, unlocked state, available funding, and verified deployment data. Simulate the exact claim immediately before signing, then request only that call with `value: 0n`. Refresh checks when the account/chain changes and invalidate stale responses.

The pinned contract never sets a swept marker and does not update round accounting when sweeping. Its balance is shared across rounds, and one permitted sweep drains the entire distributor balance. `funded - claimed` alone therefore does not prove tokens remain available. Neither passing the sweep time nor a historical zero-amount sweep proves a wallet has lost eligibility. Confirm current funding, logs, and simulation; do not invent a boolean to bridge the contract's limitation. Independent review must address the multi-round sweep concern in [launch-handoff.md](launch-handoff.md).

Show wallet balance, allocated rewards, and currently claimable WORK separately. Disconnected, wrong-chain, absent, locked (with unlock time), claimed, funding unavailable/swept, signing, pending, confirmed, and recoverable RPC/signature/revert errors are distinct states. A failed read is unknown, never zero balance or not eligible. A confirmed claim requires a successful receipt, then fresh `claimed` and balance reads; transaction submission alone is not success. The future frontend tests these states with mocked wallets/RPCs, including rejected signing and reverted transactions, without worker broadcasts.

## ABI hashes and site inventory

`python3 scripts/export_abis.py --check` checks both raw ABI arrays and [abi-hashes.json](abi-hashes.json). The canonical ABI digest is Keccak-256 over UTF-8 JSON with recursively sorted object keys, preserved array order, and no whitespace. The export tool matches the platform canonicalizer for these ASCII ABI values. It is distinct from SHA-256 of the pretty-printed ABI file. Compare the **token canonical ABI digest** to the actual handoff `abiHash`; no handoff exists here, so that comparison awaits deployment.

The later `dist/imd-deployment.json` must copy the exact attested contract set, names, addresses, ABI hashes, launch ID, source commit, chain, and attestation hash from the validated handoff. Load that same file at runtime. Do not add the protocol distributor to its attested `contracts` array. Inventory the distributor ABI, its separate actual-address configuration, allocation snapshot/tree, and `claims.json` as additional SHA-256-hashed assets. Include all final static files except the inventory itself, regenerate hashes after changes, and keep relative paths suitable for gateway hosting. No sample address/root/proof in this contribution is a deployment configuration.
