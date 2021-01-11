from dynaconf import LazySettings, Validator

from uptimer import ROOT_PATH

settings = LazySettings(
    DEBUG_LEVEL_FOR_DYNACONF="DEBUG",
    CORE_LOADERS_FOR_DYNACONF=["TOML", "ENV"],
    ENV_SWITCHER_FOR_DYNACONF="UPTIMER_ENV",
    ENVVAR_PREFIX_FOR_DYNACONF=False,
    LOADERS_FOR_DYNACONF=["dynaconf.loaders.env_loader"],
    ROOT_PATH_FOR_DYNACONF=ROOT_PATH,
    SETTINGS_FILE_FOR_DYNACONF="settings.toml,.secrets.toml",
)

settings.validators.register(
    # Ensure writer plugin exists
    Validator("WRITER_PLUGIN", must_exist=True),
    # Ensure reader plugin exists, but only when queue plugin does not
    Validator("READER_PLUGIN", must_exist=True, when=Validator("QUEUE_PLUGIN", eq="")),
)
settings.validators.validate()
