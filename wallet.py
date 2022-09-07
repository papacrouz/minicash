# Don't trust me with cryptography.

import random
import hashlib

import requests
from ecc.curve import secp256k1, Point
import b_dhke
from proof_util import proof_serialize, proof_deserialize
import lmdb

from walletdb import WalletDB, CWalletExtDB
import baseutil
import context

class LedgerAPI:
    def __init__(self, url):
        self.url = url
        self.keys = self._get_keys(url)

    @staticmethod
    def _get_keys(url):
        resp = requests.get(url + '/keys').json()
        return {
            int(amt): Point(val["x"], val["y"], secp256k1)
            for amt, val in resp.items()
        }

    @staticmethod
    def _get_output_split(amount):
        """Given an amount returns a list of amounts returned e.g. 13 is [1, 4, 8]."""
        bits_amt = bin(amount)[::-1][:-2]
        rv = []
        for (pos, bit) in enumerate(bits_amt):
            if bit == "1":
                rv.append(2**pos)
        return rv
    
    def _construct_proofs(self, promises, secrets):
        """Returns proofs of promise from promises."""
        proofs = []
        for promise, (r, secret_msg) in zip(promises, secrets):
            C_ = Point(promise["C'"]["x"], promise["C'"]["y"], secp256k1)
            C = b_dhke.step3_bob(C_, r, self.keys[promise["amount"]])
            proofs.append({
                "amount": promise["amount"],
                "C": {
                    "x": C.x,
                    "y": C.y,
                },
                "secret_msg": secret_msg,
            })
        return proofs

    def mint(self, nCoins):
        """Mints new coins and returns a proof of promise."""
        secret_msg = str(random.getrandbits(128))
        # why does the server needs to store secrete in plaintext ?
        # server only needs to learn about secrete't only when consume proofs
        # in order to create new promises.
        # so hash the secrete before pass it to server.
        secret_msg_hashed = hashlib.sha256(secret_msg.encode()).hexdigest()

        B_, r = b_dhke.step1_bob(secret_msg_hashed)

        promise = requests.post(self.url + "/mint", json={"x": str(B_.x), "y": str(B_.y),  "C": str(nCoins)}).json()
        return self._construct_proofs([promise], [(r, secret_msg_hashed)])[0], secret_msg

    def split(self, proofs, actual_secrets, amount):
        """Consume proofs and create new promises based on amount split."""
        total = sum([p["amount"] for p in proofs])
        fst_amt, snd_amt = total-amount, amount
        fst_outputs = self._get_output_split(fst_amt)
        snd_outputs = self._get_output_split(snd_amt)


        secretMap = {} # hashed -> actual 

        secrets = []
        output_data = []
        for output_amt in fst_outputs:
            # may we end with new promises here.
            # Server must not learn about actual secret's.

            secret_msg = str(random.getrandbits(128))
            # hash the secret
            secret_msg_hashed = hashlib.sha256(secret_msg.encode()).hexdigest()

            B_, r = b_dhke.step1_bob(secret_msg_hashed)

            secrets.append((r, secret_msg_hashed))
            output_data.append({
                "amount": output_amt,
                "B'": {
                    "x": B_.x,
                    "y": B_.y,
                },
            })


            # map only our change
            secretMap[secret_msg_hashed] = secret_msg


        for output_amt in snd_outputs:
    
            secret_msg = str(random.getrandbits(128))
            # hash the secret
            secret_msg_hashed = baseutil.Hash(secret_msg)

            B_, r = b_dhke.step1_bob(secret_msg_hashed)

            secrets.append((r, secret_msg_hashed))
            output_data.append({
                "amount": output_amt,
                "B'": {
                    "x": B_.x,
                    "y": B_.y,
                },
            })

            

        promises = requests.post(self.url + "/split", json={
            "proofs": proofs, 
            "amount": amount, 
            "output_data": output_data, 
            "secrets": actual_secrets}
        ).json()
        

        if "error" in promises:
            print("Failure: {}".format(promises["error"]))
            return [], [], False, False

        # Obtain proofs from promises
        fst_proofs = self._construct_proofs(promises["fst"], secrets[:len(promises["fst"])])
        snd_proofs = self._construct_proofs(promises["snd"], secrets[len(promises["fst"]):])

        return fst_proofs, snd_proofs, True, secretMap


class Wallet(LedgerAPI):
    """Minimal wallet wrapper."""
    def __init__(self, url):
        super().__init__(url)
  
       

    def mint(self, nCoins=64):
        proof, secret_msg = super().mint(nCoins)

        # add proof on memory, runtime.
        context.proofs.append(proof)


        with WalletDB() as walletdb:
            walletdb.WriteProof(proof)



        # the proof of promise received by the server, cointains the secrete message hashed.
        # so when when we want to split the newly mint proof, we have to provide a pattern than 
        # hash to proof secrete message.

        index = baseutil.Hash(proof).encode()


        # store the plaintext secrete message on memory 
        context.proofs_secrets[index] = secret_msg

        with WalletDB() as walletdb:
            walletdb.WriteSecret(index, secret_msg.encode())

        
        # the proof 

        return proof

    def split(self, proofs, amount):

        


        # get the actual secrete's for each proof.
        actual_secrets = [self.get_proof_secrete(proof) for proof in context.proofs]


        fst_proofs, snd_proofs, success, secrets = super().split(proofs, actual_secrets, amount)

        if not success:
            return [], [], False


        txdb = WalletDB(f_txn=True)
        txdb.txn_begin()

        used_secret_msgs = [p["secret_msg"] for p in proofs]
        context.proofs = list(filter(lambda p: p["secret_msg"] not in used_secret_msgs, context.proofs))
        context.proofs += fst_proofs

        # As author notes the split function consumes proofs of promise 
        # and creates new promises based on the split amount.



        # After a split we may end with a new proof of promise's
        # store new proofs of promise's on db.
        for proof in fst_proofs:
            # be sure that we have the actual secrete
            assert(proof["secret_msg"] in secrets)
            # get the actual secrete for proof 
            secrete_plain_text = secrets[proof["secret_msg"]]
            # calculate proof hash 
            index = baseutil.Hash(proof).encode()
            # store the proof actual secrete on memory, runtime use. 
            context.proofs_secrets[index] = secrete_plain_text

            # store proof, and its plain text secrete message on wallet db, for next use. 

            txdb.WriteProof(proof)
            txdb.WriteSecret(index, secrete_plain_text.encode())
                


        # Mark consumed proofs of promise as used. 
        for used_secret in used_secret_msgs:
            index = baseutil.Hash(used_secret).encode()
            txdb.WriteUsedProof(index, used_secret.encode())


        txdb.txn_commit()

        return fst_proofs, snd_proofs, True

    def balance(self):
        return sum(p["amount"] for p in context.proofs)

    def status(self):
        print("Balance: {}".format(self.balance()))

    def proof_amounts(self):
        return [p["amount"] for p in sorted(context.proofs, key=lambda p: p["amount"])]

    def get_proofs(self):
        return context.proofs


    def get_proof_secrete(self, proof):
        index = baseutil.Hash(proof).encode()
        if not index in context.proofs_secrets:
            return False 
        return context.proofs_secrets[index]


    def load_wallet(self):
        # load wallet proofs on memory 
        wallet_db = CWalletExtDB()
        if not wallet_db.LoadWallet():
            return False

        return True
