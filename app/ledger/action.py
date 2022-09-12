from app.ledger import ledgerdb as db

from app import (
    context
)






def LoadLedger():
    # load used proofs on memory 
    ledger_db = CLedgerExtDB()
    if not ledger_db.LoadLedger():
        return False
    return True


class CLedgerExtDB(db.LedgerDB):
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