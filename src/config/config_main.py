""" Loads General Program configuration as cfg, boxed """

from box import Box
from typing import Any
import yaml

CONFIG_LOC: str = "configs/notis_config.yaml"
env = "dev"


def load_config() -> Box:
    with open(CONFIG_LOC) as fp:
        full_cfg: dict[str, Any] = yaml.safe_load(fp)

    cfg: Box = Box(
        {**full_cfg["base"], **full_cfg[env]}, default_box=True, default_box_attr=None
    )

    return cfg


cfg: Box = load_config()
