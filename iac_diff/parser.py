import hcl2
import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Resource:
    type: str
    name: str
    config: dict
    references: list[str] = field(default_factory=list)

    @property
    def id(self):
        return f"{self.type}.{self.name}"


def extract_references(config: dict) -> list[str]:
    refs = []
    def walk(obj):
        if isinstance(obj, str):
            # matches ${aws_vpc.main.id} or aws_vpc.main
            found = re.findall(r'\$\{([a-z][a-z0-9_]+\.[a-z][a-z0-9_]+)\.[^}]+\}', obj)
            refs.extend(found)
            found2 = re.findall(r'(?<!\$\{)([a-z][a-z0-9_]+\.[a-z][a-z0-9_]+)(?:\.[a-z_]+)?(?!\})', obj)
            refs.extend(found2)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k not in ('__comments__', '__is_block__'):
                    walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(config)
    return list(set(refs))


def parse_terraform(filepath: str) -> dict[str, Resource]:
    path = Path(filepath)
    with open(path, 'r') as f:
        data = hcl2.load(f)

    resources = {}
    for block in data.get('resource', []):
        for rtype, rtype_block in block.items():
            # strip surrounding quotes from resource type and name
            clean_type = rtype.strip('"')
            for rname, config in rtype_block.items():
                clean_name = rname.strip('"')
                refs = extract_references(config)
                # only keep refs that look like valid resource IDs
                valid_refs = [
                    r for r in refs
                    if r != f"{clean_type}.{clean_name}"
                    and not r.startswith('0.')
                ]
                r = Resource(
                    type=clean_type,
                    name=clean_name,
                    config=config,
                    references=valid_refs
                )
                resources[r.id] = r
    return resources