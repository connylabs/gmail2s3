import yaml
from gmail2s3.config import GCONFIG


print(yaml.safe_dump(GCONFIG.settings, indent=2))
