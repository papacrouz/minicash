import threading


fShutdown = False
listfThreadRunning = [False] * 10
fMinter = False

walletLock = threading.RLock()
proofsLock = threading.RLock()
ledgerLock = threading.RLock()

proofs = []
used_proofs = []
proofs_secrets = {}


# ledger 
ledger_used_proofs = set()
