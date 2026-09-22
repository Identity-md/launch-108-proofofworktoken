#!/usr/bin/env python3
"""Export or check compiler-derived ABIs offline. Does not deploy or contact RPCs."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def inspect(root, contract):
    result = subprocess.run(
        ["forge", "inspect", "--root", str(root), "--offline", contract, "abi", "--json"],
        cwd=root, check=True, capture_output=True, text=True,
    )
    abi = json.loads(result.stdout)
    if not isinstance(abi, list):
        raise ValueError("Expected a raw ABI array")
    return abi


def canonical_keccak(abi):
    # ABI JSON has ASCII keys/strings, integer metadata at most, and ordered arrays.
    # This matches the platform's recursive key-sort canonicalization for this domain.
    canonical = json.dumps(abi, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = subprocess.check_output(["cast", "keccak", "0x" + canonical.encode().hex()], text=True).strip()
    return digest.removeprefix("0x")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare exports without replacing them")
    args = parser.parse_args()

    token_abi = inspect(ROOT, "src/ProofOfWorkToken.sol:ProofOfWorkToken")
    reference = json.loads((ROOT / "docs/protocol/MerkleDistributor.sources.json").read_text())
    with tempfile.TemporaryDirectory(prefix="work-protocol-abi-") as directory:
        temporary = Path(directory)
        # Source is unpacked only to an ephemeral compilation project, outside launch src/.
        for name, source in reference["sources"].items():
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Invalid reference source path")
            data = source["content"].encode()
            if hashlib.sha256(data).hexdigest() != reference["sha256"][name]:
                raise ValueError(f"Reference source digest mismatch: {name}")
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (temporary / "foundry.toml").write_text(
            '[profile.default]\n'
            'solc = "0.8.26"\nevm_version = "cancun"\n'
            'optimizer = true\noptimizer_runs = 200\nvia_ir = false\n'
            'bytecode_hash = "none"\ncbor_metadata = false\n'
            'offline = true\nffi = false\nfs_permissions = []\n'
            'auto_detect_remappings = false\n'
            'remappings = ["@openzeppelin/contracts/=lib/openzeppelin-contracts/contracts/"]\n'
        )
        distributor_abi = inspect(temporary, reference["contract"])

    exports = {"ProofOfWorkToken": token_abi, "MerkleDistributor": distributor_abi}
    output = ROOT / "docs/abi"
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, abi in exports.items():
        data = (json.dumps(abi, indent=2) + "\n").encode()
        destination = output / f"{name}.json"
        if args.check:
            if not destination.exists() or destination.read_bytes() != data:
                raise SystemExit(f"ABI export is stale: {destination.relative_to(ROOT)}")
        else:
            destination.write_bytes(data)
        hashes[name] = {"canonicalKeccak256": canonical_keccak(abi), "fileSha256": hashlib.sha256(data).hexdigest()}
    hash_data = (json.dumps(hashes, indent=2) + "\n").encode()
    hash_path = ROOT / "docs/abi-hashes.json"
    if args.check:
        if not hash_path.exists() or hash_path.read_bytes() != hash_data:
            raise SystemExit("ABI hashes are stale")
    else:
        hash_path.write_bytes(hash_data)
    print("ABI exports and hashes " + ("verified" if args.check else "generated") + " offline")


if __name__ == "__main__":
    main()
