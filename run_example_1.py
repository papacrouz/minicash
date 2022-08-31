# Don't trust me with cryptography.

from wallet import Wallet


SERVER_ENDPOINT = "http://localhost:5000"
wallet = Wallet(SERVER_ENDPOINT)
print("Balance before mint: {}".format(wallet.balance()))

# Mint a proof of promise. We obtain a proof for 16 coins
proof = wallet.mint(16)
print("Bob Balance after mint: {}".format(wallet.balance()))



# Assume that bob to send 3 coins to alice 
# bob split the 16 coins proof that he mint 
# above, based on amount that he wants want to 
# send to alice 

bob_proofs, alice_proofs = wallet.split([proof], 3)
# bob_proofs = [1, 4, 8] = 13 coins balance 
# alice_proofs = [1, 2] = 3 coins balance
# bob_proofs + alice_proofs = 16 coins 
print("Bob balance after send 3 coins to Alice: {}".format(sum(p["amount"] for p in bob_proofs)))
print("Alice balance: {}".format(sum(p["amount"] for p in alice_proofs)))


# Alice spend 2 coin's to john of its 3
alice_proofs, john_proofs = wallet.split(alice_proofs, 2)
# alice_proofs = [1] = 1 coins balance 
# john_proofs = [2] = 2 coins balance
# alice_proofs + john_proofs = 3 coins, that bob sends to alice. 
print("Alice balance after send 2 coins to john: {}".format(sum(p["amount"] for p in alice_proofs)))
print("John balance: {}".format(sum(p["amount"] for p in john_proofs)))