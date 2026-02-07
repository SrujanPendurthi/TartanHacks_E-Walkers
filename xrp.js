import xrpl from "xrpl";

// XRPL testnet client
const client = new xrpl.Client("wss://s.altnet.rippletest.net:51233/");
await client.connect();

class PotGroup {
  constructor(usernames) {
    this.users = [];
    this.whitelist = [];
    this.potWallet = null;
    this.initialized = false;

    this.init(usernames);
  }

  async init(usernames) {
    // Generate pot wallet
    this.potWallet = await this.createWallet("Pot");

    // Generate user wallets
    for (const username of usernames) {
      const wallet = await this.createWallet(username);
      this.users.push({ username, wallet, balance: 0 });
      this.whitelist.push(wallet.address);
    }

    this.initialized = true;
  }

  async createWallet(name) {
    // Fund a new testnet wallet
    const fundResult = await client.fundWallet();
    console.log(`${name} -> Address: ${fundResult.wallet.address} Seed: ${fundResult.wallet.seed}`);
    return fundResult.wallet;
  }

  async depositToPot(username, amountXrp) {
    const user = this.users.find(u => u.username === username);
    if (!user) return console.log(`ERROR: User ${username} not found`);
    if (!this.whitelist.includes(user.wallet.address)) return console.log(`ERROR: ${username} not whitelisted`);

    const payment = {
      TransactionType: "Payment",
      Account: user.wallet.address,
      Amount: (amountXrp * 1_000_000).toString(),
      Destination: this.potWallet.address
    };

    const tx = await client.submitAndWait(payment, { wallet: user.wallet });
    user.balance += amountXrp;
    console.log(`${username} deposited ${amountXrp} XRP, new balance: ${user.balance}`);
    console.log(`Ledger TX hash: ${tx.result.hash}`);
  }

  async withdrawFromPot(username, amountXrp) {
    const user = this.users.find(u => u.username === username);
    if (!user) return console.log(`ERROR: User ${username} not found`);
    if (!this.whitelist.includes(user.wallet.address)) return console.log(`ERROR: ${username} not whitelisted`);
    if (amountXrp > user.balance) return console.log(`ERROR: ${username} cannot withdraw ${amountXrp} XRP — balance: ${user.balance}`);

    const payment = {
      TransactionType: "Payment",
      Account: this.potWallet.address,
      Amount: (amountXrp * 1_000_000).toString(),
      Destination: user.wallet.address
    };

    const tx = await client.submitAndWait(payment, { wallet: this.potWallet });
    user.balance -= amountXrp;
    console.log(`${username} withdrew ${amountXrp} XRP, new balance: ${user.balance}`);
    console.log(`Ledger TX hash: ${tx.result.hash}`);
  }

  printAccounts() {
    console.log("\nAll accounts:");
    for (const user of this.users) {
      console.log(`${user.username}: ${user.wallet.address} | Balance: ${user.balance}`);
    }
    console.log(`Pot: ${this.potWallet.address}`);
  }
}

// -----------------------------
// Example usage
// -----------------------------
const usernames = ["Alice", "Bob", "Carol"];
const group = new PotGroup(usernames);

// Wait for wallets to initialize
await new Promise(r => setTimeout(r, 5000));

await group.depositToPot("Alice", 10);  // Alice deposits 10 XRP
await group.withdrawFromPot("Bob", 5);  // Bob cannot withdraw
await group.depositToPot("Bob", 20);    // Bob deposits 20 XRP
await group.withdrawFromPot("Bob", 5);  // Bob can now withdraw

group.printAccounts();

await client.disconnect();
