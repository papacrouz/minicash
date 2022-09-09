#!/usr/bin/env python

# Don't trust me with cryptography. Ok.

"""
Implementation of https://gist.github.com/phyro/935badc682057f418842c72961cf096c
"""

import hashlib

from ecc.curve import secp256k1, Point
from ecc.key import gen_keypair
from py_ecc.bls import G2ProofOfPossession
from ledgerdb import LedgerDB, CLedgerExtDB

import b_dhke
import context
import baseutil
import lmdb
from key import CKey


class Ledger:
    def __init__(self, secret_key):
        self.master_key = secret_key
        self.keys = self._derive_keys(self.master_key)
        


    @staticmethod
    def _derive_keys(master_key):
        """Deterministic derivation of keys for 2^n values."""
        return {
            2**i: int(hashlib.sha256((str(master_key) + str(i)).encode("utf-8")).hexdigest().encode("utf-8"), 16)
            for i in range(20)
        }


    def _generate_promises(self, amounts, B_s):
        """Generates promises that sum to the given amount."""
        return [
            self._generate_promise(amount, Point(B_["x"], B_["y"], secp256k1))
            for (amount, B_) in zip(amounts, B_s)
        ]


    def _generate_promise(self, amount, B_):
        """Generates a promise for given amount and returns a pair (amount, C')."""
        secret_key = self.keys[amount] # Get the correct key
        return {"amount": amount, "C'": b_dhke.step2_alice(B_, secret_key)}


    def _verify_proof(self, proof):
        """Verifies that the proof of promise was issued by this ledger."""
        if proof["public_key"] in context.ledger_used_proofs:
            raise Exception("Already spent. Secret msg:{}".format(proof["public_key"]))
        secret_key = self.keys[proof["amount"]] # Get the correct key to check against
        C = Point(proof["C"]["x"], proof["C"]["y"], secp256k1)
        return b_dhke.verify(secret_key, C, proof["public_key"])


    def _verify_outputs(self, total, amount, output_data):
        """Verifies the expected split was correctly computed"""
        fst_amt, snd_amt = total-amount, amount  # we have two amounts to split to
        fst_outputs = self._get_output_split(fst_amt)
        snd_outputs = self._get_output_split(snd_amt)
        expected = fst_outputs + snd_outputs
        given = [o["amount"] for o in output_data]
        return given == expected
    

    def _verify_no_duplicates(self, proofs, output_data):
        public_keys = [p["public_key"] for p in proofs]
        if len(public_keys) != len(list(set(public_keys))):
            return False
        B_xs = [od["B'"]["x"] for od in output_data]
        if len(B_xs) != len(list(set(B_xs))):
            return False
        return True


    @staticmethod
    def _get_output_split(amount):
        """Given an amount returns a list of amounts returned e.g. 13 is [1, 4, 8]."""
        bits_amt = bin(amount)[::-1][:-2]
        rv = []
        for (pos, bit) in enumerate(bits_amt):
            if bit == "1":
                rv.append(2**pos)
        return rv

    # Public methods

    def get_pubkeys(self):
        """Returns public keys for possible amounts."""
        return {
            amt: self.keys[amt] * secp256k1.G
            for amt in [2**i for i in range(20)]
        }


    def mint(self, B_, nCoins):
        """Mints a promise for nCoins coins for B_."""
        # NOTE: This could be implemented that a mint requires a rare pow
        return self._generate_promise(nCoins, B_)

        
    def split(self, proofs, amount, output_data):
        """Consumes proofs and prepares new promises based on the amount split."""
        # Verify proofs are valid

        if not all([self._verify_proof(p) for p in proofs]):
            return False


        # get the public key for each proof 
        proof_public_keys = set([p["public_key"] for p in proofs])


        
        # Anyone can claim that owns a specifiec proof ? Does we have to trust him with a proof ? No.
        # Verify that the client have provide a proof that he knows the private key associated 
        # with Consumed proof public key.


        key = CKey()

        for proof in proofs:
            if not key.ProofVerify(proof):
                raise Exception("Proof of possesion Falied. Do you know the secrete?.")


        total = sum([p["amount"] for p in proofs])

        if not self._verify_no_duplicates(proofs, output_data):
            raise Exception("Duplicate proofs or promises.")
        if amount > total:
            raise Exception("split amount is higher than the total sum")
        if not self._verify_outputs(total, amount, output_data):
            raise Exception("Split of promises is not as expected.")

        # Perform split
        proof_public_keys = set([p["public_key"] for p in proofs])
        # Mark proofs as used and prepare new promises
        context.ledger_used_proofs |= proof_public_keys
        outs_fst = self._get_output_split(total-amount)
        outs_snd = self._get_output_split(amount)
        B_fst = [od["B'"] for od in output_data[:len(outs_fst)]]
        B_snd = [od["B'"] for od in output_data[len(outs_fst):]]

        # store used proofs on db 

        txdb = LedgerDB(f_txn=True)
        txdb.txn_begin()

        for proof in proof_public_keys:
            index = baseutil.Hash(proof).encode()
            txdb.WriteUsedProof(index, proof.encode())

        txdb.txn_commit()



        return self._generate_promises(outs_fst, B_fst), self._generate_promises(outs_snd, B_snd)




    def load_ledger(self):
        # load used proofs on memory 
        ledger_db = CLedgerExtDB()
        if not ledger_db.LoadLedger():
            return False
        return True
