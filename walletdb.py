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
    DBKEY_SECRETPROOF = B"proofsecrete:"

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
                    context.proofs.append(constructed_proof)

                elif index[0] == b"usedproof":
                    # used proof's 
                    context.used_proofs.append(value)

                elif index[0] == b"proofsecrete":
                    context.proofs_secrets[index[1]] = value
        self.close()


        
        all_ = context.proofs
        context.proofs = []
        for proof in all_:
            if not proof["secret_msg"].encode() in context.used_proofs:
                context.proofs.append(proof)

        return True