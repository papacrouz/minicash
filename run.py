#!/usr/bin/python

import sys 

from app import context 
import app.wallet.action as walletaction

import app.key.action as keyaction 



if not walletaction.LoadWallet():
	sys.exit("Failed to load wallet")


print(walletaction.GetBalance())
print(walletaction.SellectProofs(38))



print(keyaction.GenerateNewKey())

print(context.mapKeys)