import xrpl
from xrpl.wallet import generate_faucet_wallet, Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait

# XRPL testnet client
TESTNET_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(TESTNET_URL)

class PotGroup:
    def __init__(self, usernames):
        """
        usernames: list of strings
        Generates wallets for each user and the pot.
        Tracks internal balances per user.
        """
        self.users = self.createUserWallets(usernames)
        self.potWallet = self.createPotWallet()
        self.whitelist = [u["wallet"].classic_address for u in self.users]

    def createUserWallets(self, usernames):
        """Generate a testnet wallet for each username and start with 0 balance"""
        userList = []
        for username in usernames:
            wallet = generate_faucet_wallet(client)
            userList.append({"username": username, "wallet": wallet, "balance": 0})
            print(f"{username} -> Address: {wallet.classic_address} Seed: {wallet.seed}")
        return userList

    def createPotWallet(self):
        """Generate a testnet wallet for the pot"""
        wallet = generate_faucet_wallet(client)
        print(f"Pot Account -> Address: {wallet.classic_address} Seed: {wallet.seed}")
        return wallet

    def depositToPot(self, username, amountXrp):
        """Deposit XRP to the pot and increase user's internal balance"""
        user = self.getUser(username)
        if not user:
            print(f"ERROR: User {username} not found.")
            return
        if user["wallet"].classic_address not in self.whitelist:
            print(f"ERROR: {username} not whitelisted.")
            return

        payment = Payment(
            account=user["wallet"].classic_address,
            amount=str(int(amountXrp * 1_000_000)),
            destination=self.potWallet.classic_address
        )
        txResponse = submit_and_wait(payment, client, user["wallet"])
        user["balance"] += amountXrp
        print(f"{username} deposited {amountXrp} XRP, new balance: {user['balance']}")
        print(f"Ledger TX hash: {txResponse.result['hash']}")

    def withdrawFromPot(self, username, amountXrp):
        """Withdraw XRP from the pot if user's internal balance is sufficient"""
        user = self.getUser(username)
        if not user:
            print(f"ERROR: User {username} not found.")
            return
        if user["wallet"].classic_address not in self.whitelist:
            print(f"ERROR: {username} not whitelisted.")
            return
        if amountXrp > user["balance"]:
            print(f"ERROR: {username} cannot withdraw {amountXrp} XRP — balance is {user['balance']}")
            return

        payment = Payment(
            account=self.potWallet.classic_address,
            amount=str(int(amountXrp * 1_000_000)),
            destination=user["wallet"].classic_address
        )
        txResponse = submit_and_wait(payment, client, self.potWallet)
        user["balance"] -= amountXrp
        print(f"{username} withdrew {amountXrp} XRP, new balance: {user['balance']}")
        print(f"Ledger TX hash: {txResponse.result['hash']}")

    def getUser(self, username):
        """Return user dict for a given username"""
        for user in self.users:
            if user["username"] == username:
                return user
        return None

    def printAccounts(self):
        """Print all addresses and internal balances"""
        print("\nAll accounts:")
        for user in self.users:
            print(f"{user['username']}: {user['wallet'].classic_address} | Balance: {user['balance']}")
        print(f"Pot: {self.potWallet.classic_address}")

# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    usernames = ["Alice", "Bob", "Carol"]
    group = PotGroup(usernames)

    group.depositToPot("Alice", 10)   # Alice deposits 10 XRP
    group.withdrawFromPot("Bob", 5)   # Bob cannot withdraw (balance=0)
    group.depositToPot("Bob", 20)     # Bob deposits 20 XRP
    group.withdrawFromPot("Bob", 5)   # Now Bob can withdraw 5 XRP

    group.printAccounts()
