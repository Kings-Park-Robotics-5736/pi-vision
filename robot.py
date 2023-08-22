import typing

import networktables


class CircleDefinition:
    x: float
    y: float
    radius: float
    anglex: float

    def __init__(self, x: float, y: float, radius: float, anglex: float):
        self.x = x
        self.y = y
        self.radius = radius
        self.anglex = anglex


class RobotConnection:
    def __init__(self, robot_ip: str, fake: bool=False):
        self.robot_ip = robot_ip
        self.fake = fake

    def connect(self):
        if self.fake:
            networktables.NetworkTables.startTestMode()
        else:
            networktables.NetworkTables.initialize(server=self.robot_ip)

    def get_table(self, table_name: str) -> networktables.NetworkTable:
        return networktables.NetworkTables.getTable(table_name)

    def put_number(self, table_name: str, key: str, value: float):
        self.get_table(table_name).putNumber(key, value)

    def put_circle(self, table_name: str, circle: typing.Optional[CircleDefinition]):
        if circle is None:
            self.put_number(table_name, "centerx", -1)
            self.put_number(table_name, "centery", -1)
            self.put_number(table_name, "radius", -1)
            self.put_number(table_name, "anglex", -1)
        else:
            self.put_number(table_name, "centerx", circle.x)
            self.put_number(table_name, "centery", circle.y)
            self.put_number(table_name, "radius", circle.radius)
            self.put_number(table_name, "anglex", circle.anglex)
