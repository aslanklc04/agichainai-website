// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/// Sabit arzlı, sahipsiz token: yeni basma, dondurma, vergi veya kara liste yok.
contract GuvenliToken is ERC20 {
    constructor(string memory ad, string memory sembol, uint256 arz) ERC20(ad, sembol) {
        _mint(msg.sender, arz * 10 ** decimals());
    }
}
