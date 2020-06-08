# Random number generator
from numpy.random import Generator, Philox, SeedSequence

class RNG:
    def __init__(self, seed):
        self.seed = seed
        self.seed_seq = SeedSequence(seed)
        self.big_gen = Philox(seed)
        self.generators = dict()

    def expand(self, name):
        """Add a Generator to the RNG Generator list.
        name - Name of new Generator, if exists will do nothing.
        """
        if name not in self.generators:
            self.generators[name] = Generator(self.big_gen)
            self.big_gen = self.big_gen.jumped()

    def get(self, name):
        """Get Generator.
        name - Name of Generator, if doesn't exist, will create it.
        """
        if name not in self.generators:
            self.expand(name)
        return self.generators[name]
