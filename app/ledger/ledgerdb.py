#!/usr/bin/env python

from app import (
    context
)

from app.db import (
    db
)



class LedgerDB(db.CDB):
    DBKEY_USEDPROOF = b"usedproof:"

    def __init__(self, f_txn=False):
        super(LedgerDB, self).__init__("ledger", f_txn)


    def WriteUsedProof(self, index, proof):
        key = self.DBKEY_USEDPROOF + index
        value = proof
        return self._write(key, value)

    
