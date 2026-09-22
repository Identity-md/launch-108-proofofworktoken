// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/// @title Proof Of Work
/// @notice Fixed supply launch token. ProjectFactory receives the complete supply at creation.
contract ProofOfWorkToken is ERC20 {
    /// @dev No arguments, privileged roles, or post-construction minting entry points.
    constructor() ERC20("Proof Of Work", "WORK") {
        _mint(msg.sender, 1_000_000_000 * 10 ** 18);
    }
}
