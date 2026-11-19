// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/// Sadece testler için: her transferde %1 kesen token (fee-on-transfer).
contract KesintiliToken is ERC20 {
    constructor() ERC20("Kesintili", "KES") { _mint(msg.sender, 1_000_000 ether); }
    function _update(address from, address to, uint256 value) internal override {
        if (from != address(0) && to != address(0)) {
            uint256 kesinti = value / 100;
            super._update(from, address(0xdead), kesinti);
            value -= kesinti;
        }
        super._update(from, to, value);
    }
}

/// Sadece testler için: serbestçe basılabilen basit token.
contract BasitToken is ERC20 {
    constructor(string memory s) ERC20(s, s) {}
    function bas(address to, uint256 v) external { _mint(to, v); }
}
