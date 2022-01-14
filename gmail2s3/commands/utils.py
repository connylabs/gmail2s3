import argparse
import json
import re
import copy
import os
import yaml


def ensure_value(namespace, name, value):
    if getattr(namespace, name, None) is None:
        setattr(namespace, name, value)
    return getattr(namespace, name)


class ServerHost(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, value[0])


class LoadVariables(argparse.Action):
    def _parse_cmd(self, var):
        res = {}
        try:
            return json.loads(var)
        except json.JSONDecodeError as exc:
            for cvar in var.split(","):
                split_var = re.match("(.+?)=(.+)", cvar)
                if split_var is None:
                    raise ValueError(f"Malformed variable: {cvar}") from exc
                key, value = split_var.group(1), split_var.group(2)
                res[key] = value
        return res

    def _load_from_file(self, filename, ext):
        with open(filename, "r", encoding="utf-8") as ofile:
            if ext in [".yml", ".yaml"]:
                return yaml.load(ofile.read(), Loader=yaml.SafeLoader)
            if ext == ".json":
                return json.loads(ofile.read())
            raise ValueError(
                f"File extension is not in [yaml, json, jsonnet]: {filename}"
            )

    def load_variables(self, var):
        _, ext = os.path.splitext(var)
        if ext not in [".yaml", ".yml", ".json"]:
            return self._parse_cmd(var)
        return self._load_from_file(var, ext)

    def __call__(self, parser, namespace, values, option_string=None):
        items = copy.copy(ensure_value(namespace, self.dest, {}))
        try:
            items.update(self.load_variables(values))
        except ValueError as exc:
            raise parser.error(option_string + ": " + str(exc))
        setattr(namespace, self.dest, items)
