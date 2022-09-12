from app.key import CKey
from app.wallet.walletdb import WalletDB
from app.utils.baseutil import params_check

from app import (
    context
)
@params_check(CKey)
def AddKey(key):
	with context.mapKeysLock:
		cPulicKey = key.GetPubKey()
		cPrivateKey = key.GetPrivateKey()
		context.mapKeys[cPulicKey] = cPrivateKey

	with WalletDB() as walletDB:
		walletDB.WriteKey(str(cPulicKey).encode(), str(cPrivateKey).encode())

	return True


def GenerateNewKey():
	key = CKey()
	key.MakeNewKey()

	if not AddKey(key):
		return False 
	return key.GetPubKey()