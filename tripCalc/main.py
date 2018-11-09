"""
Created on Mon Feb 26 14:33:20 2018
3
@author: avina
"""

import sys
import time

sys.path.insert(0, "lib")
sys.path.insert(0, "etc")

import conf
import tripCalc as tc


if __name__ == "__main__":
    start = time.time()
    tc.calculate(conf.DATA_FILE)
    end = time.time()
    print(end-start)
   

