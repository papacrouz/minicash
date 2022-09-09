#!/usr/bin/env python

import context
import db 

class LedgerDB(db.CDB):
    DBKEY_USEDPROOF = b"usedproof:"

    def __init__(self, f_txn=False):
        super(LedgerDB, self).__init__("ledger", f_txn)


    def WriteUsedProof(self, index, proof):
        key = self.DBKEY_USEDPROOF + index
        value = proof
        return self._write(key, value)

    




class CLedgerExtDB(LedgerDB):
    def __init__(self, f_txn=False):
        super(CLedgerExtDB, self).__init__(f_txn)

    def LoadLedger(self):

        local_ledger_used = []

        cursor = self._get_cursor()
        with context.ledgerLock:
            for key, value in cursor:
                index = key.split(b":")
                if index[0] == b"usedproof":
                    local_ledger_used.append(value.decode())


        self.close()

        used_proofs = set([proof for proof in local_ledger_used])
        context.ledger_used_proofs |= used_proofs

        return True