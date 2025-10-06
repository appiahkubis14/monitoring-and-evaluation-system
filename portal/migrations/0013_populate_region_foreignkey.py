from django.db import migrations

def populate_region_foreignkey(apps, schema_editor):
    District = apps.get_model('portal', 'District')
    Region = apps.get_model('portal', 'Region')
    
    for district in District.objects.all():
        if district.reg_code:  # Use reg_code to find the region
            try:
                region_obj = Region.objects.get(reg_code=district.reg_code)
                district.region_foreignkey = region_obj
                district.save()
                print(f"Linked district '{district.district}' to region '{region_obj.region}'")
            except Region.DoesNotExist:
                print(f"Warning: Region with reg_code '{district.reg_code}' not found for district '{district.district}'")

def reverse_populate(apps, schema_editor):
    District = apps.get_model('portal', 'District')
    District.objects.all().update(region_foreignkey=None)

class Migration(migrations.Migration):
    dependencies = [
        ('portal', '0012_district_region_foreignkey'),
    ]

    operations = [
        migrations.RunPython(populate_region_foreignkey, reverse_populate),
    ]