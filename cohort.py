import csv


class Cohort:
    def __init__(self):
        self.apprentices = []

    def __contains__(self, name):
        # TODO speed this up
        for apprentice in self.apprentices:
            if name == apprentice.name:
                return True
        return False

    def get_apprentice(self, name):
        # TODO speed this up
        for apprentice in self.apprentices:
            if name == apprentice.name:
                return apprentice
        return None

    def add_apprentices(self, apprentices):
        self.apprentices = apprentices

    @property
    def apprentice_count(self):
        return len(self.apprentices)

    def to_csv(self):
        with open("out.csv", "w", newline="") as f:
            w = csv.DictWriter(
                f, fieldnames=sorted(vars(self.cohorts[0].apprentices[0]))
            )
            w.writeheader()

            for cohort in self.cohorts:
                for apprentice in cohort.apprentices:
                    w.writerow({k: getattr(apprentice, k) for k in vars(apprentice)})
