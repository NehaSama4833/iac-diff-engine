import json
from dataclasses import dataclass
from .parser import Resource

@dataclass
class ResourceChange:
    change_type: str       # "added", "removed", "modified"
    resource_id: str
    resource_type: str
    before: dict | None
    after: dict | None
    changed_keys: list[str]

    def summary(self) -> str:
        if self.change_type == "added":
            return f"[+] {self.resource_id} — new resource added"
        elif self.change_type == "removed":
            return f"[-] {self.resource_id} — resource removed"
        else:
            keys = ", ".join(self.changed_keys)
            return f"[~] {self.resource_id} — fields changed: {keys}"


def diff_resources(
    before: dict[str, Resource],
    after: dict[str, Resource]
) -> list[ResourceChange]:
    changes = []
    all_ids = set(before) | set(after)

    for rid in all_ids:
        if rid not in before:
            changes.append(ResourceChange(
                change_type="added",
                resource_id=rid,
                resource_type=after[rid].type,
                before=None,
                after=after[rid].config,
                changed_keys=list(after[rid].config.keys())
            ))
        elif rid not in after:
            changes.append(ResourceChange(
                change_type="removed",
                resource_id=rid,
                resource_type=before[rid].type,
                before=before[rid].config,
                after=None,
                changed_keys=[]
            ))
        else:
            b_config = before[rid].config
            a_config = after[rid].config
            changed = [
                k for k in set(b_config) | set(a_config)
                if b_config.get(k) != a_config.get(k)
            ]
            if changed:
                changes.append(ResourceChange(
                    change_type="modified",
                    resource_id=rid,
                    resource_type=before[rid].type,
                    before=b_config,
                    after=a_config,
                    changed_keys=changed
                ))

    return changes