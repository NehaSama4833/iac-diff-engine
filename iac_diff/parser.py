import hcl2
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
    """Recursively find all resource references like aws_vpc.main.id"""
    refs = []
    def walk(obj):
        if isinstance(obj, str):
            # terraform references look like: "${aws_subnet.main.id}" or just aws_subnet.main
            import re
            found = re.findall(r'([a-z][a-z0-9_]+\.[a-z][a-z0-9_]+)', obj)
            refs.extend(found)
        elif isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(config)
    return list(set(refs))


def parse_terraform(filepath: str) -> dict[str, Resource]:
    """Parse a .tf file and return a dict of resource_id -> Resource"""
    path = Path(filepath)
    with open(path, 'r') as f:
        data = hcl2.load(f)

    resources = {}
    for block in data.get('resource', []):
        for rtype, rtype_block in block.items():
            for rname, config in rtype_block.items():
                refs = extract_references(config)
                r = Resource(
                    type=rtype,
                    name=rname,
                    config=config,
                    references=[ref for ref in refs if ref != f"{rtype}.{rname}"]
                )
                resources[r.id] = r
    return resources