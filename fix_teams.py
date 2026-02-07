import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devsync.settings')
django.setup()

from devcord.models import Team

def fix_team_names():
    # Get all teams ordered by creation date
    teams = Team.objects.all().order_by('created_at')
    seen_names = {}
    
    for team in teams:
        original_name = team.name
        counter = seen_names.get(team.name, 0) + 1
        
        if counter > 1:
            # Add a suffix to make the name unique
            team.name = f"{original_name}_{counter}"
            team.save()
            print(f"Renamed team from '{original_name}' to '{team.name}'")
        
        seen_names[original_name] = counter

if __name__ == '__main__':
    print("Starting to fix team names...")
    fix_team_names()
    print("Finished fixing team names!") 