#!/usr/bin/env python

import random

from py_ecc.bls import (
    G2ProofOfPossession
)



class CKey:

    def __init__(self):
        self._private_key = None 
        self._public_key = None
        

    def __del__(self):
        self._private_key = None

    def MakeNewKey(self):
        self._private_key = random.getrandbits(128)
        self._public_key = G2ProofOfPossession.SkToPk(self._private_key)


    def set_privkey(self, key):
        self._private_key = key 


    def GetPrivateKey(self):
        return self._private_key


    def GetPubKey(self):
        return self._public_key.hex()


    def MakeProof(self):
        return G2ProofOfPossession.PopProve(int(self._private_key))


    def ProofVerify(self, proof, proof_of_possession):
        return G2ProofOfPossession.PopVerify(bytes.fromhex(proof["public_key"]), proof_of_possession)

