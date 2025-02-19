from characters import Player
from locations import bathroom, locations

guy = Player(bathroom)

i = 0
while i < 10:
    guy.wander()
    i += 1

for location in locations:
    print(f"The Player visited the {location.name} {location.visits} times")
