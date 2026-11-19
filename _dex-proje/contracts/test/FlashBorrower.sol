pragma solidity =0.6.6;

// Sadece testler için: flash swap ve yeniden giriş (reentrancy) denemeleri.
interface IPair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function token0() external view returns (address);
    function token1() external view returns (address);
}
interface IERC20Min { function transfer(address to, uint value) external returns (bool); }

contract FlashBorrower {
    // mod: 0 = ücretle geri öde, 1 = ücretsiz geri öde (K hatası beklenir), 2 = içeriden tekrar swap dene
    uint public mod;

    function borrow(address pair, uint amount0, uint _mod) external {
        mod = _mod;
        IPair(pair).swap(amount0, 0, address(this), abi.encode(pair));
    }

    function uniswapV2Call(address, uint amount0, uint, bytes calldata data) external {
        address pair = abi.decode(data, (address));
        address t0 = IPair(pair).token0();
        if (mod == 2) {
            IPair(pair).swap(1, 0, address(this), "");
            return;
        }
        uint geri = mod == 0 ? (amount0 * 1000) / 997 + 1 : amount0;
        IERC20Min(t0).transfer(pair, geri);
    }
}
