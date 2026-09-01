class Actor:
    def __init__(self, name, characters):
        self.name = name
        self.characters = characters
        self.WeeklyConflicts = [[0]*56 for _ in range(7)]  # 7 days, 56 time slots each]
        self.OneTimeConflicts = [[0]*56 for _ in range(7)]  # 7 days, 56 time slots each]
        self.allConflicts = [[self.WeeklyConflicts[i][j] or self.OneTimeConflicts[i][j] for j in range(56)] for i in range(7)]

        def update_all_conflicts(self):
            self.allConflicts = [[self.WeeklyConflicts[i][j] or self.OneTimeConflicts[i][j] for j in range(56)] for i in range(7)]