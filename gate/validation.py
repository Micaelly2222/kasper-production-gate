"""Reject malformed containers/configuration before producing any decisions.

Empty or missing business fields still reach the gate and produce clarification
messages. Invalid JSON shapes are input errors, not client business decisions.
"""


def string(value, path, *, nonempty=False):
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise ValueError(f"{path} must be {'a nonempty' if nonempty else 'a'} string")


def string_list(value, path):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{path} must be an array of strings")


def record(value, path):
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")


def counts(value, path):
    record(value, path)
    for kind in ("statics", "videos"):
        number = value.get(kind)
        if type(number) is not int or number < 0:
            raise ValueError(f"{path}.{kind} must be a non-negative integer")


def validate_inputs(briefs, clients):
    for name, value in (("briefs", briefs), ("clients", clients)):
        if not isinstance(value, list):
            raise ValueError(f"{name} must be an array")
    for index, brief in enumerate(briefs):
        path = f"briefs[{index}]"
        record(brief, path)
        for field in ("id", "created_at"):
            string(brief.get(field), f"{path}.{field}", nonempty=True)
        for field in ("client", "title", "copy_direction", "notes", "assets_link"):
            string(brief.get(field, ""), f"{path}.{field}")
        for field in ("platforms", "formats", "products"):
            string_list(brief.get(field, []), f"{path}.{field}")
        if "use_studio_catalog" in brief and type(brief["use_studio_catalog"]) is not bool:
            raise ValueError(f"{path}.use_studio_catalog must be boolean")
        comments = brief.get("comments", [])
        if not isinstance(comments, list):
            raise ValueError(f"{path}.comments must be an array")
        for number, comment in enumerate(comments):
            location = f"{path}.comments[{number}]"
            record(comment, location)
            for field in ("by", "at", "text"):
                string(comment.get(field), f"{location}.{field}")
    for index, client in enumerate(clients):
        path = f"clients[{index}]"
        record(client, path)
        for field in ("client", "squad_lead", "status"):
            string(client.get(field), f"{path}.{field}", nonempty=True)
        for field in ("banned_claims", "brain_rules"):
            string_list(client.get(field), f"{path}.{field}")
            if any(not item.strip() for item in client[field]):
                raise ValueError(f"{path}.{field} cannot contain empty policies")
        for field in ("plan_per_month", "used_this_month"):
            counts(client.get(field), f"{path}.{field}")
        cap = client.get("max_discount_pct")
        if type(cap) not in (int, float) or not 0 <= cap <= 100:
            raise ValueError(f"{path}.max_discount_pct must be between 0 and 100")
        if not isinstance(client.get("catalog"), list):
            raise ValueError(f"{path}.catalog must be an array")
        for number, product in enumerate(client["catalog"]):
            location = f"{path}.catalog[{number}]"
            record(product, location)
            for field in ("sku", "name"):
                string(product.get(field), f"{location}.{field}", nonempty=True)
            string_list(product.get("aliases", []), f"{location}.aliases")
            if type(product.get("active")) is not bool:
                raise ValueError(f"{location}.active must be boolean")
