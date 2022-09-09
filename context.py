import threading


fShutdown = False
listfThreadRunning = [False] * 10
fMinter = False

walletLock = threading.RLock()
proofsLock = threading.RLock()


# wallet 
wallet_proofs = []
wallet_used_proofs = []
wallet_proofs_keys = {}


# ledger 
ledger_used_proofs = set()
ledgerLock = threading.RLock()

