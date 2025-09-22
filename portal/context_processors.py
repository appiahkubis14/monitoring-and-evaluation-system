from django.contrib.auth.decorators import login_required
# from .models import SidebarMenu
from utils import sidebar







from django.contrib.auth.decorators import login_required
# from .models import SidebarMenu

def user_has_any_group(user_group_names, allowed_groups):
    """Check if user has any of the allowed groups"""
    return bool(set(user_group_names) & set(allowed_groups))

def filter_sidebar_level(items, user_group_names, user):
    """Recursively filter sidebar items based on user groups"""
    filtered_items = {}

    for item_name, item_data in items.items():
        allowed_groups = item_data.get("groups", [])
        
        # Check if user has required groups
        if allowed_groups and not user_has_any_group(user_group_names, allowed_groups):
            continue  # Skip this item
        
        # Recursively filter nested sub-items if any
        sub_items = item_data.get("sub_items", {})
        filtered_sub_items = filter_sidebar_level(sub_items, user_group_names, user) if sub_items else {}

        # Create the item dictionary
        item_dict = {
            "icon": item_data.get("icon"),
        }
        
        if "url" in item_data:
            item_dict["url"] = item_data["url"]
        
        # Only include sub_items if they are not empty
        if filtered_sub_items:
            item_dict["sub_items"] = filtered_sub_items
        
        # Only add the item to filtered_items if it has content (url or valid sub_items)
        if "url" in item_dict or filtered_sub_items:
            filtered_items[item_name] = item_dict

    return filtered_items

def sidebar_context(request):
    """Generate sidebar context based on user roles"""
    if not request.user.is_authenticated:
        return {}

    user_groups = request.user.groups.all()
    user_group_names = set(user_groups.values_list('name', flat=True))

    filtered_sidebar_items = filter_sidebar_level(
        sidebar.Sidebar.sidebar_items,
        user_group_names,
        request.user
    )

    # print(filtered_sidebar_items)

    return {
        "sidebar_items": filtered_sidebar_items,
        "path": request.path,
        "current_user": request.user
    }