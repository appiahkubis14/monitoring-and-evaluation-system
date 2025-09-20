# from django.contrib.auth.models import Group
# from employees.models import Employee

# def get_sidebar_for_user(user):
#     # Define the sidebar structure as we did before
#     sidebar_items = {
#         "Dashboard Overview": {
#             "icon": "fas fa-desktop",
#             "sub_items": {
#                 "Company dashboard": {"icon": "fa fa-truck", "url": "/dashboard/home/", "groups": ["Admin", "Manager", "Warehouse Manager"]},
#                 "Transport Dashboard": {"icon": "fa fa-truck", "url": "/dashboard/transport/", "groups": ["Transport Manager", "Logistics Coordinator", "Fleet Supervisor"]},
#                 "Inventory Dashboard": {"icon": "fa fa-boxes", "url": "/dashboard/inventory/", "groups": ["Inventory Manager", "Warehouse Manager"]},
#                 "Warehouse Dashboard": {"icon": "fa fa-warehouse", "url": "/dashboard/warehouse/", "groups": ["Warehouse Supervisor", "Warehouse Manager"]},
#                 "Tracking Dashboard": {"icon": "fa fa-map-marked-alt", "url": "/dashboard/tracking/", "groups": ["Logistics Coordinator", "Manager"]},
#             },
#         },

#         "Employees Management": {
#             "icon": "fa fa-users",
#             "sub_items": {
#                 "View Employees": {"icon": "fa fa-list", "url": "/employees/employee-list/", "groups": ["Admin", "Manager", "Director"]},
#                 "Requested Inventories": {"icon": "fa fa-plus", "url": "/employees/requested-inventory/", "groups": ["Inventory Manager"]},
#                 "Manage Departments": {"icon": "fa fa-building", "url": "/employees/departments/", "groups": ["Admin", "Manager", "Director"]},
#                 "Assign Roles": {"icon": "fa fa-user-shield", "url": "/employees/roles/", "groups": ["Admin"]},
#             },
#         },

#         "Inventory Management": {
#             "icon": "fa fa-box-open",
#             "sub_items": {
#                 "View All Inventory": {"icon": "fa fa-list", "url": "/inventory/view-inventories/", "groups": ["Inventory Manager", "Warehouse Manager"]},
#                 "Inventory Requests": {"icon": "fa fa-plus", "url": "/inventory/requested-inventory/", "groups": ["Inventory Manager", "Warehouse Manager"]},
#                 "Inventory Transactions": {"icon": "fa fa-exclamation-circle", "url": "/inventory/transactions/", "groups": ["Inventory Manager"]},
#             },
#         },

#         "Warehouse Operations": {
#             "icon": "fa fa-warehouse",
#             "sub_items": {
#                 "Warehouse Overview": {"icon": "fa fa-info-circle", "url": "/warehouse/overview/", "groups": ["Warehouse Supervisor", "Warehouse Manager", "Admin"]},
#                 "Storage Management": {"icon": "fa fa-box", "url": "/warehouse/storage/", "groups": ["Warehouse Supervisor", "Warehouse Manager"]},
#                 "Inbound Shipments": {"icon": "fa fa-arrow-down", "url": "/warehouse/inbound/", "groups": ["Warehouse Supervisor", "Warehouse Manager"]},
#                 "Outbound Shipments": {"icon": "fa fa-arrow-up", "url": "/warehouse/outbound/", "groups": ["Warehouse Supervisor", "Warehouse Manager"]},
#             },
#         },

#         "Transport & Logistics": {
#             "icon": "fa fa-truck",
#             "sub_items": {
#                 "Fleet Overview": {"icon": "fa fa-car-side", "url": "/transport/vehicles/", "groups": ["Transport Manager", "Fleet Supervisor"]},
#                 "Dispatch Overview": {"icon": "fa fa-calendar", "url": "/transport/delivery_schedule/", "groups": ["Fleet Supervisor", "Transport Manager"]},
#                 "Fleet Management": {"icon": "fa fa-user-tag", "url": "/transport/driver_assistant_assignment/", "groups": ["Transport Manager", "Fleet Supervisor"]},
#                 "Client Request Records": {"icon": "fa fa-handshake", "url": "/transport/client-requests/", "groups": ["Transport Manager", "Logistics Coordinator"]},
#                 "Maintenance Records": {"icon": "fa fa-tools", "url": "/transport/maintenance-request/", "groups": ["Fleet Maintenance Technician", "Transport Manager"]},
#                 "Requested Inventories": {"icon": "fa fa-plus", "url": "/transport/inventory/view/", "groups": ["Transport Manager", "Inventory Manager"]},
#             },
#         },

#         "Real-Time Tracking": {
#             "icon": "fa fa-map",
#             "sub_items": {
#                 "Track Vehicles": {"icon": "fa fa-truck-moving", "url": "/tracking/vehicles/", "groups": ["Logistics Coordinator", "Transport Manager", "Fleet Supervisor"]},
#                 "Track Shipments": {"icon": "fa fa-shipping-fast", "url": "/tracking/shipments/", "groups": ["Logistics Coordinator", "Transport Manager"]},
#                 "Route Optimization": {"icon": "fa fa-route", "url": "/tracking/routes/", "groups": ["Transport Manager", "Logistics Coordinator"]},
#                 "Historical Route Data": {"icon": "fa fa-history", "url": "/tracking/history/", "groups": ["Transport Manager", "Logistics Coordinator"]},
#             },
#         },

#         "Insights & Reports": {
#             "icon": "fa fa-chart-line",
#             "sub_items": {
#                 "Sales Reports": {"icon": "fa fa-file-invoice-dollar", "url": "/reports/sales/", "groups": ["Admin", "Manager", "Director"]},
#                 "Stock Reports": {"icon": "fa fa-clipboard-list", "url": "/reports/stock/", "groups": ["Inventory Manager", "Warehouse Manager", "Admin"]},
#                 "Transport Efficiency": {"icon": "fa fa-road", "url": "/reports/transport/", "groups": ["Transport Manager", "Fleet Supervisor"]},
#                 "Warehouse Utilization": {"icon": "fa fa-boxes", "url": "/reports/warehouse/", "groups": ["Warehouse Manager", "Warehouse Supervisor"]},
#             },
#         },

#         "Security & Access Control": {
#             "icon": "fa fa-shield-alt",
#             "sub_items": {
#                 "User Roles & Permissions": {"icon": "fa fa-user-shield", "url": "/security/roles/", "groups": ["Admin", "Director"]},
#                 "Login History & Logs": {"icon": "fa fa-history", "url": "/security/logs/", "groups": ["Admin", "Manager"]},
#                 "Two-Factor Authentication": {"icon": "fa fa-lock", "url": "/security/2fa/", "groups": ["Admin", "Manager", "Director"]},
#             },
#         },

#         "Settings & Configuration": {
#             "icon": "fa fa-cogs",
#             "sub_items": {
#                 "User Accounts": {"icon": "fa fa-user-cog", "url": "/settings/users/", "groups": ["Admin", "Manager"]},
#                 "System Preferences": {"icon": "fa fa-sliders-h", "url": "/settings/system/", "groups": ["Admin"]},
#                 "Notifications & Alerts": {"icon": "fa fa-bell", "url": "/settings/notifications/", "groups": ["Admin", "Manager"]},
#             },
#         },

#         "Logout": {
#             "icon": "fa fa-sign-out-alt",
#             "url": "/logout/",
#             "groups": ["Admin", "Manager", "Warehouse Manager", "Transport Manager", "Logistics Coordinator", "Inventory Manager", "Director", "Fleet Supervisor", "Warehouse Supervisor"]
#         }
#     }

#     visible_sidebar = {}
#     # Get user groups
#     user_groups = set(user.groups.values_list('name', flat=True))
    
#     # Iterate over sidebar items
#     for section_name, section_data in sidebar_items.items():
#         # Filter sub-items based on user groups
#         filtered_sub_items = {
#             sub_item_name: sub_item_data
#             for sub_item_name, sub_item_data in section_data.get("sub_items", {}).items()
#             if user_groups.intersection(sub_item_data["groups"])
#         }
        
#         # If there are visible sub-items, add them to the sidebar
#         if filtered_sub_items:
#             visible_sidebar[section_name] = {
#                 "icon": section_data["icon"],
#                 "sub_items": filtered_sub_items
#             }
    
#     return visible_sidebar