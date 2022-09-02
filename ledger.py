# Don't trust me with cryptography.

"""
Implementation of https://gist.github.com/phyro/935badc682057f418842c72961cf096c
"""

import hashlib

from ecc.curve import secp256k1, Point
from ecc.key import gen_keypair

import b_dhke
import lmdb


class Ledger:
    def __init__(self, secret_key):
        self.master_key = secret_key
        self.used_proofs = set()  # no promise proofs have been used
        self.keys = self._derive_keys(self.master_key)
        self.env = lmdb.open('proofs.lmdb', max_dbs=10)
        self.used_proof_db = self.env.open_db(b'used_proofs')


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
        if proof["secret_msg"] in self.used_proofs:
            raise Exception("Already spent. Secret msg:{}".format(proof["secret_msg"]))
        secret_key = self.keys[proof["amount"]] # Get the correct key to check against
        C = Point(proof["C"]["x"], proof["C"]["y"], secp256k1)
        return b_dhke.verify(secret_key, C, proof["secret_msg"])

    def _verify_outputs(self, total, amount, output_data):
        """Verifies the expected split was correctly computed"""
        fst_amt, snd_amt = total-amount, amount  # we have two amounts to split to
        fst_outputs = self._get_output_split(fst_amt)
        snd_outputs = self._get_output_split(snd_amt)
        expected = fst_outputs + snd_outputs
        given = [o["amount"] for o in output_data]
        return given == expected
    
    def _verify_no_duplicates(self, proofs, output_data):
        secret_msgs = [p["secret_msg"] for p in proofs]
        if len(secret_msgs) != len(list(set(secret_msgs))):
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

    def split(self, proofs, amount, output_data, secrets):
        """Consumes proofs and prepares new promises based on the amount split."""
        # Verify proofs are valid

        if not all([self._verify_proof(p) for p in proofs]):
            return False


        # get the hashed secrete msg for each prrof 
        proof_msgs = set([p["secret_msg"] for p in proofs])


        # does client have the correct secret's ?
        for secret in secrets:
            hashed_secrete = hashlib.sha256(secret.encode()).hexdigest()
            if not hashed_secrete in proof_msgs:
                raise Exception("Secrete calculation mistatch. Do you know the secrete?.")
                return False


        total = sum([p["amount"] for p in proofs])

        if not self._verify_no_duplicates(proofs, output_data):
            raise Exception("Duplicate proofs or promises.")
        if amount > total:
            raise Exception("split amount is higher than the total sum")
        if not self._verify_outputs(total, amount, output_data):
            raise Exception("Split of promises is not as expected.")

        # Perform split
        proof_msgs = set([p["secret_msg"] for p in proofs])
        # Mark proofs as used and prepare new promises
        self.used_proofs |= proof_msgs
        outs_fst = self._get_output_split(total-amount)
        outs_snd = self._get_output_split(amount)
        B_fst = [od["B'"] for od in output_data[:len(outs_fst)]]
        B_snd = [od["B'"] for od in output_data[len(outs_fst):]]

        # store used proofs on db 

        for proof in proof_msgs:
            index = hashlib.sha256(proof.encode()).hexdigest().encode()
            key = b"usedproof:" + index
            with self.env.begin(write=True) as txn:
                txn.put(key, proof.encode(), db=self.used_proof_db)


        return self._generate_promises(outs_fst, B_fst), self._generate_promises(outs_snd, B_snd)






    def load_ledger(self):
        # load used proofs on memory 
        db_used = []
        with self.env.begin() as txn:
             for key, value in txn.cursor(self.used_proof_db):
                index = key.split(b":")
                if index[0] == b"usedproof":
                    db_used.append(value.decode())

        used_proofs = set([proof for proof in db_used])
        self.used_proofs |= used_proofs
        return True
