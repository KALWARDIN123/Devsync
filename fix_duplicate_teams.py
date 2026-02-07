from django.db import connection

def fix_duplicate_team_names():
    # Get all teams with duplicate names
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name, COUNT(*) as count, GROUP_CONCAT(id) as ids
            FROM devcord_team 
            GROUP BY name 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        # Process each set of duplicates
        for name, count, ids in duplicates:
            id_list = ids.split(',')
            # Skip the first one (keep original name)
            for i, team_id in enumerate(id_list[1:], 1):
                # Update others with a suffix
                cursor.execute("""
                    UPDATE devcord_team 
                    SET name = ? 
                    WHERE id = ?
                """, [f"{name}_{i}", team_id])

if __name__ == '__main__':
    fix_duplicate_team_names()
    print("Duplicate team names have been fixed!") 