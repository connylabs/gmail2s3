from gmail2s3.openapi import openapi
from gmail2s3.commands.command_base import CommandBase


class OpenapiCmd(CommandBase):
    name = "openapi"
    help_message = "show openapis"
    output_default = "yaml"

    def __init__(self, options):
        super().__init__(options)
        self.openapi = None

    @classmethod
    def _add_arguments(cls, parser):
        pass

    def _call(self):
        self.openapi = openapi()

    def _render_dict(self):
        return self.openapi

    def _render_console(self):
        return self.openapi
