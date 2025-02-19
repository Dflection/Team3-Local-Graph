from random import choice
from locations import bathroom


class Player:
    def __init__(self, starting_location):
        self.location = starting_location

    def __repr__(self):
        return f"The Player is in {self.location.name}"

    def wander(self):
        self.location.visits += 1
        # pick a random adjacent room
        goal = choice(self.location.adjacent_rooms)
        print(f"The Player leaves the {self.location.name} and enters the {goal.name}")
        self.location = goal


if __name__ == "__main__":
    guy = Player(bathroom)
    print(guy)
