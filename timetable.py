class Timetable:
    def __init__(self, entries):
        self.entries = entries
        self.spawned = set()

    def check_spawns(self, sim_time):
        new_trains = []
        for e in self.entries:
            if e["id"] not in self.spawned and sim_time >= e["start_time"]:
                new_trains.append(e)
                self.spawned.add(e["id"])
        return new_trains
