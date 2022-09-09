#!/usr/bin/env python

# Don't trust me with cryptography. Ok.

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
from key import CKey

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
    
    def _construct_proofs(self, promises, public_keys):
        """Returns proofs of promise from promises."""
        proofs = []
        for promise, (r, public_key) in zip(promises, public_keys):
            C_ = Point(promise["C'"]["x"], promise["C'"]["y"], secp256k1)
            C = b_dhke.step3_bob(C_, r, self.keys[promise["amount"]])
            proofs.append({
                "amount": promise["amount"],
                "C": {
                    "x": C.x,
                    "y": C.y,
                },
                "public_key": public_key,
            })
        return proofs

    def mint(self, nCoins, key):
        """Mints new coins and returns a proof of promise."""

        B_, r = b_dhke.step1_bob(key.GetPubKey())

        promise = requests.post(self.url + "/mint", json={"x": str(B_.x), "y": str(B_.y),  "C": str(nCoins)}).json()
        return self._construct_proofs([promise], [(r, key.GetPubKey())])[0]

    def split(self, proofs, amount):
        """Consume proofs and create new promises based on amount split."""
        total = sum([p["amount"] for p in proofs])
        fst_amt, snd_amt = total-amount, amount
        fst_outputs = self._get_output_split(fst_amt)
        snd_outputs = self._get_output_split(snd_amt)


        keysMap = {} # public key -> private key 

        public_keys = []
        output_data = []
        for output_amt in fst_outputs:

            # may we end with new promises here.

            # generate a key 

            key = CKey()
            key.MakeNewKey()

            private_key = key.GetPrivateKey()
            public_key = key.GetPubKey()


            B_, r = b_dhke.step1_bob(public_key)

            public_keys.append((r, public_key))
            output_data.append({
                "amount": output_amt,
                "B'": {
                    "x": B_.x,
                    "y": B_.y,
                },
            })


            # map only our change
            keysMap[public_key] = private_key


        for output_amt in snd_outputs:

            # Todo, reciptien hard coded. 

            key = CKey()
            key.MakeNewKey()

            private_key = key.GetPrivateKey()
            public_key = key.GetPubKey()

            B_, r = b_dhke.step1_bob(public_key)

            public_keys.append((r, public_key))
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
            "output_data": output_data}).json()
        

        if "error" in promises:
            print("Failure: {}".format(promises["error"]))
            return [], [], False, False

        # Obtain proofs from promises
        fst_proofs = self._construct_proofs(promises["fst"], public_keys[:len(promises["fst"])])
        snd_proofs = self._construct_proofs(promises["snd"], public_keys[len(promises["fst"]):])

        return fst_proofs, snd_proofs, True, keysMap


class Wallet(LedgerAPI):
    """Minimal wallet wrapper."""
    def __init__(self, url):
        super().__init__(url)
  
       

    def mint(self, nCoins=64):


        # generate a key 
        key = CKey()
        key.MakeNewKey()

        # mint a proof 
        proof = super().mint(nCoins, key)

        # add proof on memory, for runtime use.
        context.wallet_proofs.append(proof)



        # store the proof on wallet db, for next use.
        with WalletDB() as walletdb:
            walletdb.WriteProof(proof)


        # Each proof of promise, cointains a public key.
        # so when when we want to split the newly mint proof, 
        # we have to provide a proof that we own the private key 
        # associated with the proof public key  
        
        
        # Calculate proof hash.
        index = baseutil.Hash(proof).encode()


        # store the plaintext privatekey on memory, for runtime use.
        # proof hash -> private key  
        context.wallet_proofs_keys[index] = key.GetPrivateKey()
        
        # store the proof private key on wallet db, for next use.
        # proof hash -> private key
        with WalletDB() as walletdb:
            walletdb.WriteSecret(index, str(key.GetPrivateKey()).encode())

        
        # the proof 

        return proof

    def split(self, proofs, amount):

        # consumes proofs of promise

        for proof in proofs:
            # get the private key associated with proof 
            priv_key = self.get_proof_secrete(proof)

            key = CKey()
            key.set_privkey(priv_key)
            # build a proof that we own the private key associated with proof public key
            proof_of_possession = key.MakeProof()
            # be sure that the proof is valid 
            assert(key.ProofVerify(proof, proof_of_possession))
            # attach the proof of possession of key ownership on actual proof.
            proof["proof_of_possession"] = proof_of_possession.hex()
        


        fst_proofs, snd_proofs, success, private_keys = super().split(proofs, amount)

        if not success:
            return [], [], False


        txdb = WalletDB(f_txn=True)
        txdb.txn_begin()

        used_secret_msgs = [p["public_key"] for p in proofs]
        context.wallet_proofs = list(filter(lambda p: p["public_key"] not in used_secret_msgs, context.wallet_proofs))
        context.wallet_proofs += fst_proofs

        # As author notes the split function consumes proofs of promise 
        # and creates new promises based on the split amount.



        # After a split we may end with a new proof of promise's
        # store new proofs of promise's on db.
        for proof in fst_proofs:
            # be sure that we have the private key
            assert(proof["public_key"] in private_keys)
            # get the actual private key for proof 
            private_key = private_keys[proof["public_key"]]
            # calculate proof hash 
            index = baseutil.Hash(proof).encode()
            # store the proof actual secrete on memory, runtime use. 
            context.wallet_proofs_keys[index] = private_key

            # store proof, and its plain text private key on wallet db, for next use. 

            txdb.WriteProof(proof)
            txdb.WriteSecret(index, str(private_key).encode())
                


        # Mark consumed proofs of promise as used. 
        for used_secret in used_secret_msgs:
            index = baseutil.Hash(used_secret).encode()
            txdb.WriteUsedProof(index, used_secret.encode())


        txdb.txn_commit()

        return fst_proofs, snd_proofs, True

    def balance(self):
        return sum(p["amount"] for p in context.wallet_proofs)

    def status(self):
        print("Balance: {}".format(self.balance()))

    def proof_amounts(self):
        return [p["amount"] for p in sorted(context.wallet_proofs, key=lambda p: p["amount"])]

    def get_proofs(self):
        return context.wallet_proofs


    def get_proof_secrete(self, proof):
        index = baseutil.Hash(proof).encode()
        if not index in context.wallet_proofs_keys:
            return False 
        return context.wallet_proofs_keys[index]


    def load_wallet(self):
        # load wallet proofs on memory 
        wallet_db = CWalletExtDB()
        if not wallet_db.LoadWallet():
            return False

        return True
