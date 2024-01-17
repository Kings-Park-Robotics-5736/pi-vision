import enum
import json
import pathlib
import typing


class ImageShow(enum.Enum):
    COLOR_FILTER = 1
    RGB = 2
    MORPHOLOGY = 3
    MEDIAN_BLUR =4
    BLOB_AND_ELLIPSE = 5

class Orientation(enum.Enum):
    RIGHTSIDE_UP = 0
    UPSIDE_DOWN = 1

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
    image_show: ImageShow



    def __init__(self, red1: HSVColorRange, red2: HSVColorRange, img_show:ImageShow, orientation:Orientation):
        self.red1 = red1
        self.red2 = red2
        self.image_show=img_show
        self.orientation = orientation

    def to_json(self):
        return {
            "red1": self.red1.to_json(),
            "red2": self.red2.to_json(),
            "image_show": {
                "value": self.image_show.name,
                "context": ValueContext(
                    type="ENUM",
                    name="Image To Show",
                    value_min=None,
                    value_max=None,
                    allowed_values=[imgshow.name for imgshow in ImageShow],
                    value_step=None,
                ).to_json(),
            },"orientation": {
                "value": self.orientation.name,
                "context": ValueContext(
                    type="ENUM",
                    name="Camera Orientation",
                    value_min=None,
                    value_max=None,
                    allowed_values=[ori.name for ori in Orientation],
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
        elif key == "image_show":
            self.image_show = ImageShow[update.value]
        elif key == "orientation":
            self.orientation = Orientation[update.value]
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
            img_show=ImageShow[json_dict["image_show"]["value"]] if "image_show" in json_dict else ImageShow.RGB,
            orientation=Orientation[json_dict["orientation"]["value"]] if "orientation" in json_dict else Orientation.RIGHTSIDE_UP,
        )


class HoughCircleContext:
    min_area: int
    min_circularity: float
    min_convexity: float
    min_inertia: float

    def __init__(self, min_area: float, min_circ: float, min_conv: float, min_inertia: float,):
        self.min_area = int(min_area)
        self.min_circularity = float(min_circ)
        self.min_convexity = float(min_conv)
        self.min_inertia = float(min_inertia)

    def to_json(self):
        return {
            "min_area": {
                "value": self.min_area,
                "context": ValueContext(
                    type="NUMBER",
                    name="Min Area",
                    value_min=0,
                    value_max=5000,
                    allowed_values=None,
                    value_step=1,
                ).to_json(),
            },
            "min_circularity": {
                "value": self.min_circularity,
                "context": ValueContext(
                    type="NUMBER",
                    name="Min Circularity",
                    value_min=0,
                    value_max=1,
                    allowed_values=None,
                    value_step=.01,
                ).to_json(),
            },
            "min_convexity": {
                "value": self.min_convexity,
                "context": ValueContext(
                    type="NUMBER",
                    name="Min Convexity",
                    value_min=0,
                    value_max=1,
                    allowed_values=None,
                    value_step=.01,
                ).to_json(),
            },
            "min_inertia": {
                "value": self.min_inertia,
                "context": ValueContext(
                    type="NUMBER",
                    name="Min Inertia",
                    value_min=0,
                    value_max=1,
                    allowed_values=None,
                    value_step=0.01,
                ).to_json(),
            }
        }

    def update(self, update: "AppContextUpdate"):
        keys = update.key.split(".", 1)
        key = keys[0]
        rest = ""
        if len(keys) > 1:
            rest = keys[1]
        if key == "min_area":
            self.min_inertia = float(update.value)
        elif key == "min_circularity":
            self.min_circularity = int(update.value)
        elif key == "min_convexity":
            self.min_convexity = int(update.value)
        elif key == "min_inertia":
            self.min_inertia = float(update.value)
        else:
            raise ValueError(f"Unknown key {update.key}")

    @staticmethod
    def from_json(json_dict: dict):
        return HoughCircleContext(
            min_area=json_dict["min_area"]["value"] if "min_area" in json_dict else 250,
            min_circ=json_dict["min_circularity"]["value"] if "min_circularity" in json_dict else 0.5,
            min_conv=json_dict["min_convexity"]["value"] if "min_convexity" in json_dict else 0.5,
            min_inertia=json_dict["min_inertia"]["value"] if "min_inertia" in json_dict else 0.1
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
        circle_context = HoughCircleContext(min_area=250, min_circ=.5, min_conv=.5, min_inertia=.1),
        color_context = ColorContext(
            red1=HSVColorRange(
                lower=HSVColor(h=0, s=90, v=0),
                upper=HSVColor(h=17, s=255, v=255)
            ),
            red2=HSVColorRange(
                lower=HSVColor(h=170, s=90, v=0),
                upper=HSVColor(h=180, s=255, v=255)
            ),           
            img_show=ImageShow.RGB,
            orientation=Orientation.RIGHTSIDE_UP
        ),
    )



if __name__ == "__main__":
    context = get_default_app_context()
    context.color_context.red1.lower.h = 10
    save_app_context(pathlib.Path("test.json"), context)
    print(load_app_context(pathlib.Path("test.json")).color_context.red1.lower.h)
