def build_menu_tree(items):
    def serialize(item):
        return {
            "id": item.id,
            "name": item.name,
            "icon": item.icon,
            "url": item.url,
            "menu_type": item.menu_type,
            "order": item.order,
            "children": []
        }

    item_map = {}
    root_items = []

    for item in items:
        item_map[item.id] = serialize(item)

    for item in items:
        if item.parent_id:
            parent = item_map[item.parent_id]
            parent["children"].append(item_map[item.id])
        else:
            root_items.append(item_map[item.id])

    # Optionally sort children by order
    for item in root_items:
        item["children"].sort(key=lambda x: x["order"])

    return root_items
