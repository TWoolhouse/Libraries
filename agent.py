from vector import Vector

class Agent:

    def __init__(self, x, y, max_speed=0.5, max_force=0.000025, breaking=100):
        self.pos = Vector(x, y)
        self.vel = Vector(0, 0)
        self.acc = Vector(0, 0)
        self.max_speed = max_speed
        self.max_force = max_force
        self.breaking = breaking
        self.tar = Vector(0, 0)

    def force(self, force):
        """Adds a Vector to the acceleration of the Agent"""
        self.acc += force

    def _update(self):
        self.vel += self.acc
        self.vel = self.vel.limit(self.max_speed)
        self.pos += self.vel

    def seek(self, target, arrive=False):
        """Returns a Vector of the needed force to reach the target Vector"""
        self.tar = target
        desired = target-self.pos
        distance = desired.mag()
        desired = desired.norm()*self.max_speed
        if arrive and distance < self.breaking:
            desired *= distance/self.breaking
        steer = (desired-self.vel).limit(self.max_force)
        return steer

    def flee(self, target):
        """Returns a Vector of the needed force to flee from the target Vector"""
        return -1*self.seek(target, False)

    def pursuit(self, target, vision):
        """Returns a Vector of the needed force to reach the target Agent at a certain distance infront of the target"""
        return self.seek(target.pos+target.vel*vision, False)
