# from random import choice


class Location:
    def __init__(self, name):
        self.name = name
        self.visits = 0

    def narrate(self):
        print(f"The {self.name} is connected to {self.adjacent_rooms}")

    def set_adjacent_rooms(self, adjacent_rooms):
        self.adjacent_rooms = adjacent_rooms


bathroom = Location("Bathroom")
hall = Location("Hall")
lounge = Location("Lounge")
rumpus_room = Location("Rumpus Room")
bar = Location("Bar")
ball_room = Location("Ball Room")

bathroom.set_adjacent_rooms([hall])
hall.set_adjacent_rooms([bathroom, lounge, ball_room, bar])
lounge.set_adjacent_rooms([hall, bar])
rumpus_room.set_adjacent_rooms([bar])
bar.set_adjacent_rooms([hall, lounge, rumpus_room])
ball_room.set_adjacent_rooms([hall])

locations = [bathroom, hall, lounge, rumpus_room, bar, ball_room]
