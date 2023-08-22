import enum
import json
import pathlib
import typing


class TeamColor(enum.Enum):
    RED = 1
    BLUE = 2


class AppContextUpdate(typing.NamedTuple):
    key: str
    value: typing.Any

    @staticmethod
    def from_json(json_dict: dict):
        return AppContextUpdate(
            key=json_dict["key"],
            value=json_dict["value"],
        )


class ValueContext:
    type: str
    name: str
    value_min: typing.Optional[float]
    value_max: typing.Optional[float]
    allowed_values: typing.Optional[typing.List[str]]
    value_step: typing.Optional[float]

    def __init__(self, type: str, name: str, value_min: typing.Optional[float], value_max: typing.Optional[float],
                    allowed_values: typing.Optional[typing.List[str]], value_step: typing.Optional[float]):
        self.type = type
        self.name = name
        self.value_min = value_min
        self.value_max = value_max
        self.allowed_values = allowed_values
        self.value_step = value_step

    def to_json(self):
        return {
            "type": self.type,
            "name": self.name,
            "value_min": self.value_min,
            "value_max": self.value_max,
            "allowed_values": self.allowed_values,
            "value_step": self.value_step,
        }


class HSVColor:
    h: int
    s: int
    v: int

    def __init__(self, h: int, s: int, v: int):
        self.h = int(h)
        self.s = int(s)
        self.v = int(v)

    def to_json(self):
        return {
            "h": {
                "value": self.h,
                "context": ValueContext(
                    type="NUMBER",
                    name="H",
                    value_min=0,
                    value_max=180,
                    allowed_values=None,
                    value_step=1,
                ).to_json(),
            },
            "s": {
                "value": self.s,
                "context": ValueContext(
                    type="NUMBER",
                    name="S",
                    value_min=0,
                    value_max=255,
                    allowed_values=None,
                    value_step=1,
                ).to_json(),
            },
            "v": {
                "value": self.v,
                "context": ValueContext(
                    type="NUMBER",
                    name="V",
                    value_min=0,
                    value_max=255,
                    allowed_values=None,
                    value_step=1,
                ).to_json(),
            },
        }

    def update(self, update: "AppContextUpdate"):
        keys = update.key.split(".", 1)
        key = keys[0]
        rest = ""
        if len(keys) > 1:
            rest = keys[1]
        if key == "h":
            self.h = int(update.value)
        elif key == "s":
            self.s = int(update.value)
        elif key == "v":
            self.v = int(update.value)
        else:
            raise ValueError(f"Unknown key {update.key}")

    @staticmethod
    def from_json(json_dict: dict):
        return HSVColor(
            h=json_dict["h"]["value"] if "h" in json_dict else 0,
            s=json_dict["s"]["value"] if "s" in json_dict else 0,
            v=json_dict["v"]["value"] if "v" in json_dict else 0,
        )


class HSVColorRange:
    lower: HSVColor
    upper: HSVColor

    def __init__(self, lower: HSVColor, upper: HSVColor):
        self.lower = lower
        self.upper = upper

    def to_json(self):
        return {
            "lower": self.lower.to_json(),
            "upper": self.upper.to_json(),
        }

    def update(self, update: "AppContextUpdate"):
        keys = update.key.split(".", 1)
        key = keys[0]
        rest = ""
        if len(keys) > 1:
            rest = keys[1]
        if key == "lower":
            self.lower.update(AppContextUpdate(rest, update.value))
        elif key == "upper":
            self.upper.update(AppContextUpdate(rest, update.value))
        else:
            raise ValueError(f"Unknown key {update.key}")

    @staticmethod
    def from_json(json_dict: dict):
        return HSVColorRange(
            lower=HSVColor.from_json(json_dict["lower"]) if "lower" in json_dict else HSVColor(h=0, s=0, v=0),
            upper=HSVColor.from_json(json_dict["upper"]) if "upper" in json_dict else HSVColor(h=0, s=0, v=0),
        )


class ColorContext:
    red1: HSVColorRange
    red2: HSVColorRange

    blue: HSVColorRange

    team: TeamColor

    def __init__(self, red1: HSVColorRange, red2: HSVColorRange, blue: HSVColorRange, team: TeamColor):
        self.red1 = red1
        self.red2 = red2
        self.blue = blue
        self.team = team

    def to_json(self):
        return {
            "red1": self.red1.to_json(),
            "red2": self.red2.to_json(),
            "blue": self.blue.to_json(),
            "team": {
                "value": self.team.name,
                "context": ValueContext(
                    type="ENUM",
                    name="Team",
                    value_min=None,
                    value_max=None,
                    allowed_values=[team.name for team in TeamColor],
                    value_step=None,
                ).to_json(),
            },
        }

    def update(self, update: "AppContextUpdate"):
        keys = update.key.split(".", 1)
        key = keys[0]
        rest = ""
        if len(keys) > 1:
            rest = keys[1]
        if key == "red1":
            self.red1.update(AppContextUpdate(rest, update.value))
        elif key == "red2":
            self.red2.update(AppContextUpdate(rest, update.value))
        elif key == "blue":
            self.blue.update(AppContextUpdate(rest, update.value))
        elif key == "team":
            self.team = TeamColor[update.value]
        else:
            raise ValueError(f"Unknown key {update.key}")

    @staticmethod
    def from_json(json_dict: dict):
        return ColorContext(
            red1=HSVColorRange.from_json(json_dict["red1"]) if "red1" in json_dict else HSVColorRange(
                lower=HSVColor(h=0, s=0, v=0),
                upper=HSVColor(h=0, s=0, v=0),
            ),
            red2=HSVColorRange.from_json(json_dict["red2"]) if "red2" in json_dict else HSVColorRange(
                lower=HSVColor(h=0, s=0, v=0),
                upper=HSVColor(h=0, s=0, v=0),
            ),
            blue=HSVColorRange.from_json(json_dict["blue"]) if "blue" in json_dict else HSVColorRange(
                lower=HSVColor(h=0, s=0, v=0),
                upper=HSVColor(h=0, s=0, v=0),
            ),
            team=TeamColor[json_dict["team"]["value"]] if "team" in json_dict else TeamColor.RED,
        )


class HoughCircleContext:
    dp: float
    param1: int
    param2: int

    circle_filter_b: float
    circle_filter_m: int

    def __init__(self, dp: float, param1: int, param2: int, circle_filter_b: float, circle_filter_m: int):
        self.dp = dp
        self.param1 = int(param1)
        self.param2 = int(param2)
        self.circle_filter_b = circle_filter_b
        self.circle_filter_m = int(circle_filter_m)

    def to_json(self):
        return {
            "dp": {
                "value": self.dp,
                "context": ValueContext(
                    type="NUMBER",
                    name="dp",
                    value_min=1,
                    value_max=2,
                    allowed_values=None,
                    value_step=0.1,
                ).to_json(),
            },
            "param1": {
                "value": self.param1,
                "context": ValueContext(
                    type="NUMBER",
                    name="param1",
                    value_min=0,
                    value_max=300,
                    allowed_values=None,
                    value_step=1,
                ).to_json(),
            },
            "param2": {
                "value": self.param2,
                "context": ValueContext(
                    type="NUMBER",
                    name="param2",
                    value_min=0,
                    value_max=255,
                    allowed_values=None,
                    value_step=1,
                ).to_json(),
            },
            "circle_filter_b": {
                "value": self.circle_filter_b,
                "context": ValueContext(
                    type="NUMBER",
                    name="circle_filter_b",
                    value_min=0,
                    value_max=50,
                    allowed_values=None,
                    value_step=0.25,
                ).to_json(),
            },
            "circle_filter_m": {
                "value": self.circle_filter_m,
                "context": ValueContext(
                    type="NUMBER",
                    name="circle_filter_m",
                    value_min=0,
                    value_max=100,
                    allowed_values=None,
                    value_step=1,
                ).to_json(),
            },
        }

    def update(self, update: "AppContextUpdate"):
        keys = update.key.split(".", 1)
        key = keys[0]
        rest = ""
        if len(keys) > 1:
            rest = keys[1]
        if key == "dp":
            self.dp = float(update.value)
        elif key == "param1":
            self.param1 = int(update.value)
        elif key == "param2":
            self.param2 = int(update.value)
        elif key == "circle_filter_b":
            self.circle_filter_b = float(update.value)
        elif key == "circle_filter_m":
            self.circle_filter_m = int(update.value)
        else:
            raise ValueError(f"Unknown key {update.key}")

    @staticmethod
    def from_json(json_dict: dict):
        return HoughCircleContext(
            dp=json_dict["dp"]["value"] if "dp" in json_dict else 1,
            param1=json_dict["param1"]["value"] if "param1" in json_dict else 79,
            param2=json_dict["param2"]["value"] if "param2" in json_dict else 13,
            circle_filter_b=json_dict["circle_filter_b"]["value"] if "circle_filter_b" in json_dict else 2,
            circle_filter_m=json_dict["circle_filter_m"]["value"] if "circle_filter_m" in json_dict else 75,
        )


class AppContext:
    color_context: ColorContext
    circle_context: HoughCircleContext

    def __init__(self, color_context: ColorContext, circle_context: HoughCircleContext):
        self.color_context = color_context
        self.circle_context = circle_context

    def to_json(self):
        return {
            "color_context": self.color_context.to_json(),
            "circle_context": self.circle_context.to_json(),
        }

    def update(self, update: AppContextUpdate):
        keys = update.key.split(".", 1)
        key = keys[0]
        rest = ""
        if len(keys) > 1:
            rest = keys[1]
        if key == "color_context":
            self.color_context.update(AppContextUpdate(rest, update.value))
        elif key == "circle_context":
            self.circle_context.update(AppContextUpdate(rest, update.value))
        else:
            raise ValueError(f"Unknown key {update.key}")

    @staticmethod
    def from_json(json_dict: dict):
        return AppContext(
            color_context=ColorContext.from_json(json_dict["color_context"]),
            circle_context=HoughCircleContext.from_json(json_dict["circle_context"]),
        )


def dump_app_context(app_context: AppContext):
    return json.dumps(app_context.to_json(), indent=2, sort_keys=True)


def save_app_context(file: pathlib.Path, app_context: AppContext):
    with file.open("w") as f:
        json.dump(app_context.to_json(), f, indent=2, sort_keys=True)


def load_app_context(file: pathlib.Path) -> AppContext:
    try:
        with file.open("r") as f:
            return AppContext.from_json(json.load(f))
    except:
        return get_default_app_context()


def get_default_app_context() -> AppContext:
    return AppContext(
        circle_context = HoughCircleContext(dp=1, param1=79, param2=13, circle_filter_b=2, circle_filter_m=75),
        color_context = ColorContext(
            red1=HSVColorRange(
                lower=HSVColor(h=0, s=90, v=0),
                upper=HSVColor(h=17, s=255, v=255)
            ),
            red2=HSVColorRange(
                lower=HSVColor(h=170, s=90, v=0),
                upper=HSVColor(h=180, s=255, v=255)
            ),
            blue=HSVColorRange(
                lower=HSVColor(h=95, s=75, v=46),
                upper=HSVColor(h=115, s=255, v=255)
            ),
            team=TeamColor.RED,
        ),
    )



if __name__ == "__main__":
    context = get_default_app_context()
    context.color_context.red1.lower.h = 10
    save_app_context(pathlib.Path("test.json"), context)
    print(load_app_context(pathlib.Path("test.json")).color_context.red1.lower.h)
