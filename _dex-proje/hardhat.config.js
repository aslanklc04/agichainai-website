require("@nomicfoundation/hardhat-ethers");
require("./solc-local");

const { PRIVATE_KEY, RPC_URL } = process.env;

module.exports = {
  solidity: {
    compilers: [
      { version: "0.5.16", settings: { optimizer: { enabled: true, runs: 999999 }, evmVersion: "istanbul" } },
      { version: "0.6.6",  settings: { optimizer: { enabled: true, runs: 999999 }, evmVersion: "istanbul" } },
      { version: "0.8.24", settings: { optimizer: { enabled: true, runs: 200 } } },
    ],
  },
  networks: {
    hardhat: process.env.YEREL_CHAIN_ID ? { chainId: Number(process.env.YEREL_CHAIN_ID) } : {},
    // Herhangi bir EVM ağı: Sepolia (test), Ethereum, BNB Chain, Base, Arbitrum...
    hedef: {
      url: RPC_URL || "http://127.0.0.1:8545",
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
  },
};

// Kod kapsamı (coverage) ölçümü için: npx hardhat coverage
try { require("solidity-coverage"); } catch (e) {}
