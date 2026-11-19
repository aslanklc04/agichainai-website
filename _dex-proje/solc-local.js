// Derleyicileri internetten indirmek yerine npm'deki solc paketlerinden kullanır.
// (İnternet erişimi olan bir bilgisayarda bu dosya gerekmez ama zararı da yoktur.)
const { subtask } = require("hardhat/config");
const { TASK_COMPILE_SOLIDITY_GET_SOLC_BUILD } = require("hardhat/builtin-tasks/task-names");
const path = require("path");

const yerel = { "0.5.16": "solc0516", "0.6.6": "solc066", "0.8.24": "solc0824" };

subtask(TASK_COMPILE_SOLIDITY_GET_SOLC_BUILD, async ({ solcVersion }, hre, runSuper) => {
  const paket = yerel[solcVersion];
  if (!paket) return runSuper();
  try {
    const compilerPath = path.join(__dirname, "node_modules", paket, "soljson.js");
    const solc = require(path.join(__dirname, "node_modules", paket));
    return { compilerPath, isSolcJs: true, version: solcVersion, longVersion: solc.version().replace(".Emscripten.clang", "") };
  } catch (e) {
    return runSuper();
  }
});
