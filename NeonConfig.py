# -*- coding: utf-8 -*-

import os
from qfluentwidgets import qconfig, QConfig, ConfigItem, BoolValidator, ConfigValidator, OptionsConfigItem, \
    OptionsValidator, ColorConfigItem


class Config(QConfig):
    Theme = OptionsConfigItem("MainWindow", "Theme", "Auto", OptionsValidator(["Light", "Dark", "Auto"]))
    ThemeColor = ColorConfigItem("MainWindow", "ThemeColor", "#0179D4")
    AutoRun = ConfigItem("MainWindow", "AutoRun", True, BoolValidator())

    IsWeather = ConfigItem("Widget", "IsWeather", True, BoolValidator())
    IsMotto = ConfigItem("Widget", "IsMotto", True, BoolValidator())
    IsCountdown = ConfigItem("Widget", "IsCountdown", True, BoolValidator())
    SpinCycle = ConfigItem("Widget", "SpinCycle", "01:00", ConfigValidator())

    Event = ConfigItem("Countdown", "Event", "", ConfigValidator())
    Date = ConfigItem("Countdown", "Date", "", ConfigValidator())

    FontFamily = ConfigItem("Curriculum", "FontFamily", "Segoe UI", ConfigValidator())
    FontSizeBig = ConfigItem("Curriculum", "FontSizeBig", 24, ConfigValidator())
    FontSizeSmall = ConfigItem("Curriculum", "FontSizeSmall", 14, ConfigValidator())
    Mon = ConfigItem("Curriculum", "Mon", [], ConfigValidator())
    Tue = ConfigItem("Curriculum", "Tue", [], ConfigValidator())
    Wed = ConfigItem("Curriculum", "Wed", [], ConfigValidator())
    Thu = ConfigItem("Curriculum", "Thu", [], ConfigValidator())
    Fri = ConfigItem("Curriculum", "Fri", [], ConfigValidator())
    Sat = ConfigItem("Curriculum", "Sat", [], ConfigValidator())
    Sun = ConfigItem("Curriculum", "Sun", [], ConfigValidator())


YEAR = "2026"
VERSION = "1.5.5"
cfg = Config()
qconfig.load(os.path.join(os.path.expanduser('~'), '.Neon', 'config', 'config.json'), cfg)
