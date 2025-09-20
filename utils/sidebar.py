

from enum import Enum

class Sidebar:
    sidebar_items = {
        "Dashboard Overview": {
            "icon": "fas fa-chart-pie",
            "sub_items": {
                "Transport & Logistics": {
                    "icon": "fas fa-truck", 
                    "url": "/dashboard/transport/", 
                    "groups": ["Admin", "Director", "Transport Manager", "Logistics Coordinator", "Fleet Supervisor"]
                },
                "Inventory Dashboard": {
                    "icon": "fas fa-boxes", 
                    "url": "/dashboard/inventory/", 
                    "groups": ["Admin", "Director", "Inventory Manager", "Inventory Assistant"]
                },
                "Warehouse Dashboard": {
                    "icon": "fas fa-warehouse", 
                    "url": "/dashboard/warehouse/", 
                    "groups": ["Admin", "Director", "Warehouse Supervisor", "Warehouse Manager"]
                },
                "Shipment Dashboard": {
                    "icon": "fas fa-shipping-fast", 
                    "url": "/dashboard/shippment/", 
                    "groups": ["Admin", "Director", "Shippment Manager", "Terminal Manager", "Forwarding Manager"]
                },
                "Tracker Dashboard": {
                    "icon": "fas fa-map-marked-alt", 
                    "url": "/dashboard/trackers/", 
                    "groups": ["Admin", "General Manager", "Director", "Tracker Manager"]
                },
                "Maintenance Dashboard": {
                    "icon": "fas fa-tools", 
                    "url": "/dashboard/maintenance/", 
                    "groups": ["Admin", "Director", "Procurement Manager"]
                },
            },
        },
        
        "Employees Management": {
            "icon": "fas fa-users-cog",
            "sub_items": {
                "View Employees": {
                    "icon": "fas fa-user-friends", 
                    "url": "/employees/employee-list/", 
                    "groups": ["Admin", "Staff Member", "Director"]
                },
            },
        },
        
        "Warehouse Operations": {
            "icon": "fas fa-pallet",
            "sub_items": {
                "Sack Transactions": {
                    "icon": "fas fa-money-bill-wave", 
                    "url": "/warehouse/sack-transactions/",
                    "groups": ["Admin", "Warehouse Manager", "Warehouse Supervisor"]
                },
                "BCG Daily Stock": {
                    "icon": "fas fa-clipboard-list", 
                    "url": "/warehouse/bcg-stock-daily/",
                    "groups": ["Admin", "Warehouse Manager", "Warehouse Supervisor"]
                },
                "Sack Totals": {
                    "icon": "fas fa-calculator", 
                    "url": "/warehouse/sack-totals/",
                    "groups": ["Admin", "Warehouse Manager", "Warehouse Supervisor"]
                },
                "Warehouse Reports": {
                    "icon": "fas fa-chart-bar", 
                    "groups": ["Admin", "Warehouse Manager", "Warehouse Supervisor"],
                    "sub_items": {
                        "All Reports": {
                            "icon": "fas fa-file-alt", 
                            "url": "/warehouse/reports/",
                            "groups": ["Admin", "Transport Manager", "Warehouse Supervisor"]
                        },
                    }
                },
            }
        },
        
        "Shipment Operations": {
            "icon": "fas fa-ship",
            "sub_items": {
                "Terminal": {
                    "icon": "fas fa-anchor", 
                    "url": "/shipment/terminal/index_terminal/",
                    "groups": ["Admin", "Terminal Manager", "Shippment Manager"]
                },
                "Forwarding": {
                    "icon": "fas fa-dolly", 
                    "url": "/shipment/forwarding/index_forwarding/",
                    "groups": ["Admin", "Shippment Manager", "Forwarding Manager"]
                },
                "Invoicing": {
                    "icon": "fas fa-file-invoice-dollar", 
                    "groups": ["Admin", "Shippment Manager", "Forwarding Manager", "Terminal Manager"],
                    "sub_items": {
                        "Terminal Invoicing": {
                            "icon": "fas fa-receipt", 
                            "url": "/shipment/terminal/index_terminal_invoicing/",
                            "groups": ["Admin", "Terminal Manager", "Shippment Manager"]
                        },
                        "Forwarding Invoicing": {
                            "icon": "fas fa-file-invoice", 
                            "url": "/shipment/forwarding/index_forwarding_invoicing/",
                            "groups": ["Admin", "Shippment Manager", "Forwarding Manager"]
                        }
                    }
                },
                "Reports": {
                    "icon": "fas fa-chart-line", 
                    "groups": ["Admin", "Shippment Manager"],
                    "sub_items": {
                        "All Reports": {
                            "icon": "fas fa-chart-pie", 
                            "url": "/shipment/reports/",
                            "groups": ["Admin", "Shippment Manager"]
                        },
                    }
                },
            }
        },
        
        "Transport & Logistics": {
            "icon": "fas fa-truck-moving",
            "sub_items": {
                "Fleet Overview": {
                    "icon": "fas fa-tachometer-alt", 
                    "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"],
                    "sub_items": {
                        "Trucks": {
                            "icon": "fas fa-truck", 
                            "url": "/transport/vehicles/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"]
                        },
                        "Fleet Management": {
                            "icon": "fas fa-clipboard-check", 
                            "url": "/transport/fleet-management/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"]
                        },
                        "Office Use Vehicles": {
                            "icon": "fas fa-car", 
                            "url": "/transport/office-use-vehicles/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"]
                        },
                    }
                },
               
                "Requests Overview": {
                    "icon": "fas fa-clipboard-list", 
                    "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"],
                    "sub_items": {
                        "Client Requests": {
                            "icon": "fas fa-envelope-open-text", 
                            "url": "/transport/client-requests/",
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"]
                        },
                        "Completed Requests": {
                            "icon": "fas fa-check-circle", 
                            "url": "/transport/waybills/",
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"]
                        },
                        "Drivers Call Up": {
                            "icon": "fas fa-user-check", 
                            "url": "/transport/drivers-call-up/",
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"]
                        },
                    }
                },

                "Inventories Overview": {
                    "icon": "fas fa-warehouse", 
                    "url": "/inventory/transactions/",
                    "groups": ["Admin", "Inventory Manager", "Inventory Assistant"],
                    "sub_items": {
                        "Spare Parts Management": {
                            "icon": "fas fa-cogs", 
                            "url": "/inventory/view-inventories/", 
                            "groups": ["Admin", "Inventory Manager", "Inventory Assistant"]
                        },
                        "Fuel Management": {
                            "icon": "fas fa-gas-pump", 
                            "url": "/inventory/vivo-energy/tanks/", 
                            "groups": ["Admin", "Inventory Manager", "Inventory Assistant"]
                        },
                        "Tires Management": {
                            "icon": "fas fa-circle", 
                            "url": "/inventory/tires/inventory-received/", 
                            "groups": ["Admin", "Inventory Manager", "Inventory Assistant"]
                        },
                        "External Activities": {
                            "icon": "fas fa-external-link-alt", 
                            "url": "/inventory/star-oil/inventory/", 
                            "groups": ["Admin", "Inventory Manager", "Inventory Assistant"]
                        },
                        "Inventory Requests": {
                            "icon": "fas fa-clipboard", 
                            "url": "/inventory/requested-inventory/", 
                            "groups": ["Admin", "Inventory Manager", "Inventory Assistant"]
                        },
                        "Inventory Transactions": {
                            "icon": "fas fa-exchange-alt", 
                            "url": "/inventory/transactions/", 
                            "groups": ["Admin", "Inventory Manager", "Inventory Assistant"]
                        },
                    },
                },
                
                "Maintenance Overview": {
                    "icon": "fas fa-wrench",
                    "sub_items": {
                        "Maintenance Categories": {
                            "icon": "fas fa-list", 
                            "url": "/transport/maintenancecategory/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor"]
                        },
                        "Maintenance Requests": {
                            "icon": "fas fa-toolbox", 
                            "url": "/transport/maintenancerequest/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator", "Mechanic"]
                        },
                        "Maintenance Tasks": {
                            "icon": "fas fa-tasks", 
                            "url": "/transport/maintenancetask/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Mechanic"]
                        },
                        "Maintenance Schedules": {
                            "icon": "fas fa-calendar-alt", 
                            "url": "/transport/maintenanceschedule/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor"]
                        },
                        "Maintenance Alerts": {
                            "icon": "fas fa-exclamation-triangle", 
                            "url": "/transport/maintenancealert/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"]
                        },
                        "Attachments": {
                            "icon": "fas fa-paperclip", 
                            "url": "/transport/maintenanceattachment/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Mechanic"]
                        }
                    }
                },
                
                "Accident Overview": {
                    "icon": "fas fa-car-crash",
                    "sub_items": {
                        "Accidents Records": {
                            "icon": "fas fa-file-medical", 
                            "url": "/transport/accident-records/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor"]
                        },
                        "Accident dashboard": {
                            "icon": "fas fa-chart-bar", 
                            "url": "/transport/accident-records-dashboard/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor"]
                        }
                    }
                },
                
                "Insights & Reports": {
                    "icon": "fas fa-chart-line",
                    "sub_items": {
                        "Reports": {
                            "icon": "fas fa-file-contract", 
                            "url": "/transport/reports/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"]
                        },
                        "Invoices": {
                            "icon": "fas fa-file-invoice", 
                            "url": "/transport/invoices/", 
                            "groups": ["Admin", "Transport Manager", "Fleet Supervisor", "Logistics Coordinator"]
                        },
                    },
                }
            },
        },
        
        "Fleet Tracking": {
            "icon": "fas fa-satellite",
            "sub_items": {
                "Realtime Tracking": {
                    "icon": "fas fa-location-arrow", 
                    "url": "http://tracker.afarinick.com/", 
                    "groups": ["Admin", "Tracker Manager"]
                },
                "Trackers Overview": {
                    "icon": "fas fa-map-marker-alt", 
                    "url": "/trackers/tracker/", 
                    "groups": ["Admin", "Tracker Manager"]
                },
                "Truck Location Updates": {
                    "icon": "fas fa-map-pin", 
                    "url": "/trackers/truck-location-updates/", 
                    "groups": ["Admin", "Tracker Manager"]
                },
                "Device Maintenance": {
                    "icon": "fas fa-cogs", 
                    "url": "/trackers/device-maintenance/", 
                    "groups": ["Admin", "Tracker Manager"]
                },
                "Reports": {
                    "icon": "fas fa-file-export",
                    "sub_items": {
                        "Fuel Theft Alerts": {
                            "icon": "fas fa-exclamation-triangle", 
                            "url": "/trackers/fuel-theft-alerts-report/", 
                            "groups": ["Admin", "Tracker Manager"]
                        },
                        "Fuel Leakage Reports": {
                            "icon": "fas fa-tint-slash", 
                            "url": "/trackers/fuel-leakage-report/", 
                            "groups": ["Admin", "Tracker Manager"]
                        },
                        "Geo Fence": {
                            "icon": "fas fa-draw-polygon", 
                            "url": "/trackers/geo-fence/", 
                            "groups": ["Admin", "Tracker Manager"]
                        },
                    }
                },
            },
        },
        
        "Security & Access Control": {
            "icon": "fas fa-shield-alt",
            "sub_items": {
                "User Roles & Permissions": {
                    "icon": "fas fa-user-lock", 
                    "url": "/security/roles/", 
                    "groups": ["Admin"]
                },
                "Login History & Logs": {
                    "icon": "fas fa-history", 
                    "url": "/security/logs/", 
                    "groups": ["Admin"]
                },
                "Two-Factor Authentication": {
                    "icon": "fas fa-lock", 
                    "url": "/security/2fa/", 
                    "groups": ["Admin"]
                },
            },
        },
        
        "Settings & Configuration": {
            "icon": "fas fa-cogs",
            "sub_items": {
                "User Accounts": {
                    "icon": "fas fa-users", 
                    "url": "/settings/users/", 
                    "groups": ["Admin", "Director", "Transport Manager", "Logistics Coordinator", "Fleet Supervisor"]
                },
                "System Preferences": {
                    "icon": "fas fa-sliders-h", 
                    "url": "/settings/system/", 
                    "groups": ["Admin", "Director", "Transport Manager", "Logistics Coordinator", "Fleet Supervisor"]
                },
                "Notifications & Alerts": {
                    "icon": "fas fa-bell", 
                    "url": "/settings/notifications/", 
                    "groups": ["Admin", "Director", "Transport Manager", "Logistics Coordinator", "Fleet Supervisor"]
                },
            },
        },
        
        "Admin Panel": {
            "icon": "fas fa-user-shield",
            "url": "/admin/",
            "groups": ["Admin"]
        }
    }