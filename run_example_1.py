# Don't trust me with cryptography.

from wallet import Wallet
import sys


SERVER_ENDPOINT = "http://localhost:5000"
wallet = Wallet(SERVER_ENDPOINT)

# load proofs from database in memory  
wallet.load_proofs()

wallet.mint(16)


# Check wallet from proofs, that match the 
# amount that we want to promise 
total = 0 
proof_to_use = [] 

while total < 10:
	for proof in wallet.proofs:
		proof_to_use.append(proof)
		total += proof["amount"]


our_proofs, alice_proofs, success = wallet.split(proof_to_use, 10)
if not success:
	sys.exit()

print("[*] After prommising 10 coins to Alice, we end with bellow proofs")

for t in our_proofs:
	print("")
	print(t)


print("")
print("[*] Our proof remaining balance {}\n".format(wallet.balance()))




print("[*] Alice ends with the bellow proofs")

for t in alice_proofs:
	print("")
	print(t)


print("[*] Alice balance {}".format(sum(p["amount"] for p in alice_proofs)))
