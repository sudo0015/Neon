from qfluentwidgets import qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator, OptionsValidator, \
    FolderValidator, RangeConfigItem, RangeValidator, EnumSerializer, ConfigValidator

class Config(QConfig):
    AutoRun = ConfigItem("MainWindow", "AutoRun", True, BoolValidator())

    Event = ConfigItem("Countdown", "Event", "", ConfigValidator())
    Date = ConfigItem("Countdown", "Date", "", ConfigValidator())

    FontFamily = ConfigItem("Curriculum", "FontFamily", "Segoe UI", ConfigValidator())
    FontColor = ConfigItem("Curriculum", "FontColor", "#0179D4", ConfigValidator())
    FontSizeBig = ConfigItem("Curriculum", "FontSizeBig", 24, ConfigValidator())
    FontSizeSmall = ConfigItem("Curriculum", "FontSizeSmall", 14, ConfigValidator())

    Mon = ConfigItem("Curriculum", "Mon", [], ConfigValidator())
    Tue = ConfigItem("Curriculum", "Tue", [], ConfigValidator())
    Wed = ConfigItem("Curriculum", "Wed", [], ConfigValidator())
    Thu = ConfigItem("Curriculum", "Thu", [], ConfigValidator())
    Fri = ConfigItem("Curriculum", "Fri", [], ConfigValidator())
    Sat = ConfigItem("Curriculum", "Sat", [], ConfigValidator())
    Sun = ConfigItem("Curriculum", "Sun", [], ConfigValidator())


YEAR = "2025"
VERSION = "1.4.0"
cfg = Config()
qconfig.load("config/config.json", cfg)
