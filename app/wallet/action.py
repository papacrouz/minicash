#!/usr/bin/python
# Copyright (c) 2022 Papa Crouz
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from app.wallet import walletdb as db


from app import (
    context
)





def GetBalance():
    total = 0
    with context.walletLock:
        for proof in context.wallet_proofs:
            total += proof["amount"]
    return total




def SellectProofs(targetValue):

    # Select the appropriate proof's from wallet according to targetValue.
    # We want 1 or more proofs with coins >= targetValue. 
    # Returns None if the total amount of coins in the wallet does not reach the targetValue.

    total = 0 

    proofsCollected = []

    for proof in context.wallet_proofs:
        proofsCollected.append(proof)
        total += proof["amount"]        

    if total < targetValue:
        # we don't have enough proofs 
        return None 


    return proofsCollected








def LoadWallet():
    wallet = CWalletExtDB()
    if not wallet.LoadWallet():
        return False 
    return True



class CWalletExtDB(db.WalletDB):
    def __init__(self, f_txn=False):
        super(CWalletExtDB, self).__init__(f_txn)

    def LoadWallet(self):

        cursor = self._get_cursor()
        with context.walletLock:
            for key, value in cursor:
                index = key.split(b":")
                if index[0] == b"proof":
                    # active proof's
                    constructed_proof = proof_deserialize(value)
                    context.wallet_proofs.append(constructed_proof)

                elif index[0] == b"usedproof":
                    # used proof's 
                    context.wallet_used_proofs.append(value)

                elif index[0] == b"proofsecrete":
                    context.wallet_proofs_keys[index[1]] = value

                elif index[0] == b"key":
                    context.mapKeys[index[1].decode()] = int(value)
        self.close()


        
        all_ = context.wallet_proofs
        context.wallet_proofs = []
        for proof in all_:
            if not proof["public_key"].encode() in context.wallet_used_proofs:
                context.wallet_proofs.append(proof)

        return True