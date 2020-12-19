import random


def roll(d=6, num=1, mod=0):
    pool = [random.randint(1, d) for i in range(num)]
    return sum(pool) + mod


def avg_roll(d=6, num=1, mod=0):
    """
    Rolls a number of dice with modifier 10000 times to git statistical average.
    """
    n = 10000
    rolls = [roll(d=d, num=num, mod=mod) for i in range(n)]
    return sum(rolls)/n


