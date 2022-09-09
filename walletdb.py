#!/usr/bin/env python


import db

import context
import hashlib

from proof_util import (
    proof_serialize, 
    proof_deserialize
)

import baseutil

class WalletDB(db.CDB):
    DBKEY_PROOF = b"proof:"
    DBKEY_USEDPROOF = b"usedproof:"
    DBKEY_SECRETPROOF = b"proofsecrete:"

    def __init__(self, f_txn=False):
        super(WalletDB, self).__init__("wallet", f_txn)


    def WriteProof(self, proof):
        # store proof on database
        serialised = proof_serialize(proof)
        index = baseutil.Hash(serialised).encode()

        key = self.DBKEY_PROOF + index
        value = serialised

        return self._write(key, value)


    def WriteSecret(self, index, secret):
        key = self.DBKEY_SECRETPROOF + index
        value = secret
        return self._write(key, value)


    def WriteUsedProof(self, index, secret):
        key = self.DBKEY_USEDPROOF + index
        value = secret
        return self._write(key, value)





class CWalletExtDB(WalletDB):
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
        self.close()


        
        all_ = context.wallet_proofs
        context.wallet_proofs = []
        for proof in all_:
            if not proof["public_key"].encode() in context.wallet_used_proofs:
                context.wallet_proofs.append(proof)

        return True
