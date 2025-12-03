# -*- coding: utf-8 -*-

from enum import Enum


class Versions(Enum):
    V2_0_0 = (2, 0, 0)
    V2_1_0 = (2, 1, 0)

if __name__ == '__main__':
    print('Available versions:')
    [print(version.value) for version in Versions.__members__.values()]

