import xrpl
from xrpl.wallet import generate_faucet_wallet, Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait

# -----------------------------
# Setup (global client only)
# -----------------------------
TESTNET_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(TESTNET_URL)

# -----------------------------
# PotGroup Class
# -----------------------------
class PotGroup:
    def __init__(self, usernames):
        self.users = self.createUserWallets(usernames)
        self.potWallet = self.createPotWallet()
        self.whitelist = [u["wallet"].classic_address for u in self.users]

    # -------------------------
    # Create user wallets
    # -------------------------
    def createUserWallets(self, usernames):
        userList = []
        for username in usernames:
            wallet = generate_faucet_wallet(client)
            print(f"{username} -> Address: {wallet.classic_address} Secret: {wallet.seed}")
            userList.append({"username": username, "wallet": wallet})
        return userList

    # -------------------------
    # Create pot wallet
    # -------------------------
    def createPotWallet(self):
        wallet = generate_faucet_wallet(client)
        print(f"Pot Account -> Address: {wallet.classic_address} Secret: {wallet.seed}")
        return wallet

    # -------------------------
    # Deposit to pot
    # -------------------------
    def depositToPot(self, username, amountXrp):
        userWallet = self.getUserWallet(username)
        if not userWallet:
            print(f"ERROR: User {username} not found.")
            return

        if userWallet.classic_address not in self.whitelist:
            print(f"ERROR: {username} ({userWallet.classic_address}) is not whitelisted.")
            return

        payment = Payment(
            account=userWallet.classic_address,
            amount=str(int(amountXrp * 1_000_000)),
            destination=self.potWallet.classic_address
        )
        txResponse = submit_and_wait(payment, client, userWallet)
        print(f"{username} paid {amountXrp} XRP to pot: {txResponse.result['hash']}")

    # -------------------------
    # Withdraw from pot
    # -------------------------
    def withdrawFromPot(self, username, amountXrp):
        userWallet = self.getUserWallet(username)
        if not userWallet:
            print(f"ERROR: User {username} not found.")
            return

        if userWallet.classic_address not in self.whitelist:
            print(f"ERROR: {username} ({userWallet.classic_address}) is not whitelisted.")
            return

        payment = Payment(
            account=self.potWallet.classic_address,
            amount=str(int(amountXrp * 1_000_000)),
            destination=userWallet.classic_address
        )
        txResponse = submit_and_wait(payment, client, self.potWallet)
        print(f"Pot sent {amountXrp} XRP to {username}: {txResponse.result['hash']}")

    # -------------------------
    # Helper: get wallet by username
    # -------------------------
    def getUserWallet(self, username):
        for user in self.users:
            if user["username"] == username:
                return user["wallet"]
        return None

    # -------------------------
    # Print all accounts
    # -------------------------
    def printAccounts(self):
        print("\nAll accounts:")
        for user in self.users:
            print(f"{user['username']}: {user['wallet'].classic_address}")
        print(f"Pot: {self.potWallet.classic_address}")


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    usernames = ["Alice", "Bob", "Carol"]
    group = PotGroup(usernames)

    # Deposit example
    group.depositToPot("Alice", 10)

    # Withdraw example
    group.withdrawFromPot("Bob", 5)

    # Print accounts
    group.printAccounts()
