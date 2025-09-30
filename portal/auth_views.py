from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_view(request):
    user = request.user
    current_hour = datetime.now().hour
    current_date = timezone.now()
    
    # Get staff information if available
    staff_info = None
    position = "-"
    
    try:
        # Check if user has a related staff record
        if hasattr(user, 'staff_user'):
            staff_info = user.staff_user.first()
            if staff_info:
                position = staff_info.designation.name if staff_info.designation else "-"
    except Exception as e:
        print(f"Error fetching staff info: {e}")
        # Fail gracefully if there's an error
    
    # Get user's permissions
    permissions = user.get_all_permissions()
    
    # Process permissions for display
    processed_permissions = []
    for perm in permissions:
        # Extract the permission name (last part after dot)
        perm_name = perm.split('.')[-1]
        # Convert to human readable format
        human_readable = perm_name.replace('_', ' ').title()
        processed_permissions.append(human_readable)
    
    # Sort permissions alphabetically
    processed_permissions.sort()
    
    context = {
        "staff_info": staff_info,
        "position": position,
        "permissions": processed_permissions,
        "current_hour": current_hour,
        "current_date": current_date,
        "user": user,
    }
    return render(request, 'portal/dashboard-index.html', context)