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

# standar 
import hashlib


# local 
import app.utils.baseutil
import context


from app.db import(
    db
)


from app.proof.proof_util import(
    proof_serialize, 
    proof_deserialize
)



class WalletDB(db.CDB):
    DBKEY_PROOF = b"proof:"
    DBKEY_USEDPROOF = b"usedproof:"
    DBKEY_SECRETPROOF = b"proofsecrete:"
    DBKEY_KEY = b"key:"

    def __init__(self, f_txn=False):
        super(WalletDB, self).__init__("wallet", f_txn)


    def WriteProof(self, proof):
        # store proof on database
        serialised = proof_serialize(proof)
        index = baseutil.Hash(serialised).encode()

        key = self.DBKEY_PROOF + index
        value = serialised

        return self._write(key, value)


    def WriteKey(self, publickey, private):
        key = self.DBKEY_KEY + publickey
        return self._write(key, private)


    def WriteSecret(self, index, secret):
        key = self.DBKEY_SECRETPROOF + index
        value = secret
        return self._write(key, value)


    def WriteUsedProof(self, index, secret):
        key = self.DBKEY_USEDPROOF + index
        value = secret
        return self._write(key, value)
