from enum import Enum

class UserRole(Enum):
    ADMIN = "Admin"
    PROJECT_MANAGER = "Project Manager"
    FIELD_OFFICER = "Field Officer"
    FARMER = "Farmer"
    STAKEHOLDER = "Stakeholder"

class Sidebar:
    sidebar_items = {
        "Dashboard": {
            "icon": "fas fa-chart-pie",
            "url": "/dashboard/",
            "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value, UserRole.STAKEHOLDER.value],
            "sub_items": {
                "Overview": {
                    "icon": "fas fa-tachometer-alt", 
                    "url": "/dashboard/overview/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.STAKEHOLDER.value]
                },
                "Performance Metrics": {
                    "icon": "fas fa-chart-line", 
                    "url": "/dashboard/performance/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                },
                "Regional Comparison": {
                    "icon": "fas fa-globe-africa", 
                    "url": "/dashboard/regional/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.STAKEHOLDER.value]
                },
            },
        },
        
        "Farmer Management": {
            "icon": "fas fa-users",
            "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value],
            "sub_items": {
                "Farmers": {
                    "icon": "fas fa-user-friends", 
                    "url": "/farmers/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value]
                },

                "Farms": {
                    "icon": "fas fa-tractor", 
                    "url": "/farmers/farms/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value]
                },
               "Monitoring": {
                    "icon": "fas fa-eye", 
                    "url": "/monitoring/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value]
                },
               
            },
        },

         "Loan Management": {
                    
                    "icon": "fas fa-hand-holding-usd", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value],
                    "sub_items": {
                        "Loan Applications": {
                            "icon": "fas fa-file-invoice-dollar", 
                            "url": "/loans/applications/", 
                            "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                        },
                        "Disbursements": {
                            "icon": "fas fa-money-check", 
                            "url": "/loans/disbursements/", 
                            "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                        },
                        "Repayment Tracking": {
                            "icon": "fas fa-chart-bar", 
                            "url": "/loans/repayments/", 
                            "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                        },
                    }
                },
        
        "Project Tracking": {
            "icon": "fas fa-tasks",
            "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value],
            "sub_items": {
                "Projects Overview": {
                    "icon": "fas fa-project-diagram", 
                    "url": "/projects/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value]
                },
                "Milestones": {
                    "icon": "fas fa-map-marker-alt", 
                    "url": "/projects/milestones/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value]
                },
                "Timeline View": {
                    "icon": "fas fa-calendar-alt", 
                    "url": "/projects/timeline/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                },
              
            }
        },
        
        "GIS Mapping": {
            "icon": "fas fa-map-marked-alt",
            "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value, UserRole.STAKEHOLDER.value],
            "sub_items": {
                "Interactive Map": {
                    "icon": "fas fa-map", 
                    "url": "/map/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value, UserRole.STAKEHOLDER.value]
                },
               
            
                # "Data Layers": {
                #     "icon": "fas fa-database", 
                #     "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value],
                #     "sub_items": {
                #         "Farm Boundaries": {
                #             "icon": "fas fa-draw-polygon", 
                #             "url": "/gis/layers/boundaries/", 
                #             "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                #         },
                #         "Irrigation Sources": {
                #             "icon": "fas fa-tint", 
                #             "url": "/gis/layers/irrigation/", 
                #             "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                #         },
                #         "Crop Health": {
                #             "icon": "fas fa-leaf", 
                #             "url": "/gis/layers/crop-health/", 
                #             "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                #         },
                #     }
                # },
                # "Spatial Analysis": {
                #     "icon": "fas fa-ruler-combined", 
                #     "url": "/gis/analysis/", 
                #     "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                # },
            }
        },
        
        "Data Collection": {
            "icon": "fas fa-mobile-alt",
            "groups": [UserRole.ADMIN.value, UserRole.FIELD_OFFICER.value],
            "sub_items": {
                "Field Forms": {
                    "icon": "fas fa-clipboard-list", 
                    "url": "/data/forms/", 
                    "groups": [UserRole.ADMIN.value, UserRole.FIELD_OFFICER.value]
                },
                "Media Upload": {
                    "icon": "fas fa-camera", 
                    "url": "/data/media/", 
                    "groups": [UserRole.ADMIN.value, UserRole.FIELD_OFFICER.value]
                },
                "Mobile Sync": {
                    "icon": "fas fa-sync", 
                    "url": "/data/sync/", 
                    "groups": [UserRole.ADMIN.value, UserRole.FIELD_OFFICER.value]
                },
            }
        },
        
        "Reports & Analytics": {
            "icon": "fas fa-chart-bar",
            "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.STAKEHOLDER.value],
            "sub_items": {
                "Standard Reports": {
                    "icon": "fas fa-file-alt", 
                    "url": "/reports/standard/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.STAKEHOLDER.value]
                },
                "Custom Reports": {
                    "icon": "fas fa-magic", 
                    "url": "/reports/custom/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                },
                "Export Center": {
                    "icon": "fas fa-file-export", 
                    "url": "/reports/export/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                },
                "KPI Dashboard": {
                    "icon": "fas fa-key", 
                    "url": "/reports/kpi/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                },
            }
        },
        
        "Communication": {
            "icon": "fas fa-comments",
            "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value],
            "sub_items": {
                "Alerts & Notifications": {
                    "icon": "fas fa-bell", 
                    "url": "/communication/alerts/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                },
                "Extension Services": {
                    "icon": "fas fa-broadcast-tower", 
                    "url": "/communication/extension/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                },
                "Message Templates": {
                    "icon": "fas fa-envelope", 
                    "url": "/communication/templates/", 
                    "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value]
                },
            }
        },
        
        "System Administration": {
            "icon": "fas fa-cogs",
            "groups": [UserRole.ADMIN.value],
            "sub_items": {
                "User Management": {
                    "icon": "fas fa-user-cog", 
                    "url": "/admin/users/", 
                    "groups": [UserRole.ADMIN.value]
                },
                "Role Permissions": {
                    "icon": "fas fa-user-lock", 
                    "url": "/admin/roles/", 
                    "groups": [UserRole.ADMIN.value]
                },
                "Data Management": {
                    "icon": "fas fa-database", 
                    "url": "/admin/data/", 
                    "groups": [UserRole.ADMIN.value]
                },
                "System Settings": {
                    "icon": "fas fa-sliders-h", 
                    "url": "/admin/settings/", 
                    "groups": [UserRole.ADMIN.value]
                },
                "Audit Logs": {
                    "icon": "fas fa-history", 
                    "url": "/admin/logs/", 
                    "groups": [UserRole.ADMIN.value]
                },
                "Admin Dashboard": {
                    "icon": "fas fa-user-shield",
                    "url": "/admin/",
                    "groups": [UserRole.ADMIN.value]
                }
            }
        },
        
        
        "Logout": {
            "icon": "fas fa-sign-out-alt",
            "url": "/logout/",
            "groups": [UserRole.ADMIN.value, UserRole.PROJECT_MANAGER.value, UserRole.FIELD_OFFICER.value, UserRole.FARMER.value, UserRole.STAKEHOLDER.value]
        },

        
    }