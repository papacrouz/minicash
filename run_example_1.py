# Don't trust me with cryptography.

from wallet import Wallet
import sys


SERVER_ENDPOINT = "http://localhost:5000"
wallet = Wallet(SERVER_ENDPOINT)

# load proofs from database in memory  
wallet.load_wallet()

# Check wallet from proofs, that match the 
# amount that we want to promise 
total = 0 
proof_to_use = []

while total < 10:
	for proof in wallet.get_proofs():
		proof_to_use.append(proof)
		total += proof["amount"]

	break


if not proof_to_use:
	sys.exit("Not available proofs to use")



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
