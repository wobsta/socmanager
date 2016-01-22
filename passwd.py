import random

random.seed()

def generate():
    return '%04d' % random.randint(0, 9999)
