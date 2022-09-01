# Don't trust me with cryptography.

from wallet import Wallet


SERVER_ENDPOINT = "http://localhost:5000"
wallet = Wallet(SERVER_ENDPOINT)

# load proofs from database in memory  
wallet.load_proofs()

if len(wallet.proofs) > 0:
	print("{} Proofs loaded from db".format(len(wallet.proofs)))

# Mint a proof of promise. We obtain a proof for 16 coins
wallet.mint(16)

# Assume that we to promise 10 coins to alice
# be sure that we have enough balance 
if wallet.balance() < 10:
	print("Not enough coins")


# Check wallet from proofs, that match the 
# amount that we want to promise 
proof_to_use = None 

for proof in wallet.proofs:
	if proof["amount"] >= 10:
		proof_to_use = proof 
		break 


print("")

print("[*] Proof to use for a promise to Alice for 10 coins contains {} coins\n".format(proof_to_use["amount"]))


print("")

our_proofs, alice_proofs = wallet.split([proof_to_use], 10)

print("[*] After prommising 10 coins to Alice, we end with bellow proofs")

for t in our_proofs:
	print("")
	print(t)


print("")
print("[*] Our proof remaining balance {}\n".format(sum(p["amount"] for p in our_proofs)))




print("[*] Alice ends with the bellow proofs")

for t in alice_proofs:
	print("")
	print(t)


print("[*] Alice balance {}".format(sum(p["amount"] for p in alice_proofs)))



