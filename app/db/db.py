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


# standard
import threading
import hashlib
import os

# istalled 
import lmdb

# local
from app.utils.baseutil import (
    GetAppDir, 
    Singleton
)


dbMutex = threading.RLock()


class CDBInit(Singleton):
    f_db_env = False

    def __init__(self):
        """
        if not os.path.exists(GetAppDir()):
            try:
                os.mkdir(GetAppDir())
            except Exception as e:
                raise RuntimeError('CDBInit() : Initialize empty data dir failed')
        """

        self.dbenv = lmdb.open('./main.lmdb', 
            map_size=int(1e8),
            max_dbs=2, 
            writemap=True, 
            metasync=False, 
            sync=False) 

        CDBInit.f_db_env = True
        self.fTest = False



    def __destroy_env(self):
        if hasattr(self, "dbenv") and self.dbenv is not None:
            self.dbenv.close()
            CDBInit.f_db_env = False
            print ("dbenv is destroyed")


    @staticmethod
    def destroy_env():
        return CDBInit().__destroy_env()


    def __getenv(self):
        if hasattr(self, "dbenv"):
            return self.dbenv
        return None


    @staticmethod
    def getEnv():
        return CDBInit().__getenv()






class CDB(object):
    def __init__(self, pszFileIn, f_txnIn):
        super(CDB, self).__init__()
        self.pszFile = pszFileIn.encode()

        self._db = None
        self.open = False

        self.f_txn = f_txnIn

        self.__txn_list = []
        self.dbenv = None


        with dbMutex:
            self.dbenv = CDBInit.getEnv()
            self._db = self.dbenv.open_db(self.pszFile)
            self.open = True


    def _write(self, key, value):
        if self._db is None:
            return
        
        """
        Sets value for key. If key exists its value is replaced even
        If key does not yet exist it will be created with the respective value.
        The changes on disk is not being updated if f_txn = True a commit() call is required.
        otherwise if f_txn is = False commit changes is done automatically.
        Params:
        key = the _key to store value for
        value = the _value to be stored for key        
        """

        if not self.f_txn:
            with self.dbenv.begin(write=True) as txn: 
                return txn.put(key, value, db=self._db)

        txn = self.get_txn()
        return txn.put(key, value)


    def _read(self, key):

        """
        Retrieves the value stored for key.
        key must neither be None nor empty.
        
        Params:
        key = the key of which the value should be returned for
        Returns: the value found for key, None if key was not found.
        """

        if not self.f_txn:
            txn = self.dbenv.begin(db=self._db)
            return txn.get(key)

        txn = self.get_txn() 
        return txn.get(key)


    def _exists(self, key):

        """
        Retrieves the value stored for key.
        key must neither be None nor empty.
        
        Params:
        key = the key of which the value should be checked if exists
        Returns: True if the value found for key, None if key was not found.
        """
        if not self._read(key):
            return False
        return True


    def _erase(self, key):

        """
        Delete the entry referred to by key. 
        Key must neither be None nor empty.
        Params:
        key = the key to be deleted from the db.
        """

        if not self.f_txn:
            txn = self.dbenv.begin(db=self._db, write=True)
            return txn.delete(key)

        txn = self.get_txn() 
        return txn.pop(key)


    def _get_cursor(self):
        txn = self.dbenv.begin(db=self._db)
        return txn.cursor()


    def get_txn(self):
        if self.__txn_list:
            return self.__txn_list[-1]
        else:
            return None


    def txn_begin(self):
        if self._db is None:
            return False

        txn = self.dbenv.begin(db=self._db, write=True)
        self.__txn_list.append(txn)
        return True


    def txn_commit(self):
        if self._db is None:
            return False
        if not self.__txn_list:
            return False
        
        txn = self.__txn_list.pop()
        ret = txn.commit()
        # TODO for txn_commit result
        #print ("txn_commit ret", ret)
        return ret == 0


    def txn_abort(self):
        if self._db is None:
            return False
        if not self.__txn_list:
            return False
        txn = self.__txn_list.pop()
        return txn.abort() == 0


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return False
        self.dbenv.sync()
        self.close()
        return True


    def __del__(self):
        self.close()


    def close(self):
        if self.open:
            self.dbenv.close()
            self.open = False

