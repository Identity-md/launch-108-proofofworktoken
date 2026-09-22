# Launch handoff

## Concrete source and manifest inputs

| Parameter | Required value |
| --- | --- |
| Launch kind | `evm_project` |
| Token artifact | `src/ProofOfWorkToken.sol:ProofOfWorkToken` |
| Solidity contract identifier | `ProofOfWorkToken` |
| ERC-20 name / symbol / decimals | `Proof Of Work` / `WORK` / `18` |
| Supply, decimal minor-unit string | `1000000000000000000000000000` |
| Token constructor arguments / ETH value | None / zero |
| Initial supply recipient | Immediate factory caller (`msg.sender`) |
| Application contracts | `contracts: []` |
| Target network | Sepolia, chain ID `11155111` |
| Pool pair | Native ETH, zero-address currency |
| Fee / tick spacing / hook | `3000` / `60` / none |
| Manifest provenance initialPrice | `79228162514264337593543950336` |
| Effective opening price | Derived by services from pinned policy v5: 20 ETH fully diluted valuation |
| Initial liquidity funding | Launch tokens only; no ETH funding |

One billion WORK at the approved opening valuation implies `0.00000002 ETH` per WORK. The manifest's legacy square-root price is preserved for provenance; the policy-derived effective price controls this launch. Do not insert a custom price, application contract, distributor, LP, game, or helper into the manifest's application list. `MerkleDistributor` is a reserved protocol artifact. The separate manifest assignment owns `launch.json`; this contribution intentionally does not generate it.

## Frozen policy and service responsibilities

The approved v5 policy allocates 2% to this launch's accepted contributors using the existing scoring process, 8% equally among unique wallets with accepted work in the preceding 12 hours, 80% to LP, and 10% to treasury. Contributor overlap is combined into a single leaf per wallet. The unlock is one hour. These are approved requirements, not a worker-generated allocation recipe: the control plane freezes the exact amounts, eligible wallets, window, rounding, root, and policy identity.

Services must select and verify the configured token-only-capable ProjectFactory on Sepolia, resolve the policy owner/treasury and distributor sweep delay, create the signed artifact linkage, and publish/attest/admit/deploy the accepted source. They verify that the factory receives the entire supply, funds the protocol distributor and LP, opens round 0, and applies the frozen splits. The token never makes these allocations itself. A direct EOA deployment would mint to that EOA and is not the authorized launch path.

The independent reviewer inspects the final source and generated manifest, including token identity, supply, constructor shape, compiler settings, empty application set, and source/constructor/policy/authorization conflicts. This document does not claim to be that review. Policy signatures and artifact linkage belong to services and need not exist to complete this implementation assignment. Concrete distributor concerns below remain review findings.

The deployment handoff must provide actual launch ID, chain, source commit, attestation hash, contract addresses, and ABI hashes. The later frontend worker discovers the protocol distributor from the launch's `artifacts` entry with role `distributor`, verifies the data described in [integration.md](integration.md), and publishes the static site through the configured services. There is no address or allocation to populate in this assignment.

Workers do not create recipients, change economic policy, access wallet keys, deploy helpers, or broadcast transactions. No mainnet transaction is authorized. Later service success and frontend publication are outside this bounded contribution.

## Assumptions and concrete review items

- ProjectFactory calls the token constructor with zero value and no arguments. Its address is not embedded in the token. The token deliberately grants no administrative role to its deployer.
- WORK follows ordinary ERC-20 semantics: failed operations revert, successful operations return `true`, maximum allowance is not reduced, and `approve` overwrites an existing allowance. Clients changing existing nonzero allowances must account for the standard approval race. The claim page never needs an approval.
- Tokens sent to the token's own address have no recovery path. The contract rejects ordinary ETH transfers, but forced ETH does not create a withdrawal right or alter the token supply.
- The protocol distributor has separate owner powers to open rounds, transfer ownership, and sweep. They do not confer token minting/admin powers. Verify actual owner, treasury, funding, and sweep delay from services and chain state.
- **Sweep semantics:** the pinned distributor's `sweep(round)` sends its entire token balance to its immutable treasury once that round's time gate allows it. It does not isolate funds by round or mark a round swept. A mature earlier round could drain a later locked round if services open one in the same distributor. Keep this as a concrete independent-review finding; the token worker cannot repair or redeploy the protocol artifact.
- `openRound` records its declared funding without enforcing actual collateral, and `claim` does not cap cumulative claims by `funded`. Services must validate snapshot totals and real funding. Unique wallets are required because claims are tracked per wallet per round, not per leaf index.

The frontend must expose unavailable funding/sweep conditions using actual reads and logs, without inventing a `swept` getter. Runtime checks and simulation reduce stale-state errors but cannot guarantee that a pending claim will execute before a later sweep.
