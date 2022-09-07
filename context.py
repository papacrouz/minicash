import threading



walletLock = threading.RLock()
proofsLock = threading.RLock()

proofs = []
used_proofs = []
proofs_secrets = {}