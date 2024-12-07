"""reorder_city_column

Revision ID: xxxxxxxxxxxx
Revises: [previous_revision_id]
Create Date: [date]
"""

# Add these lines
revision = '7a9a49e6ded0'
down_revision = '4559b6eacc3e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    # First, get the current table structure
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('restaurants')
    
    # Add safety check to drop temporary table if it exists
    op.execute("DROP TABLE IF EXISTS restaurants_new")
    
    # Create new table with same structure but reordered columns
    column_definitions = []
    for col in columns:
        if col['name'] != 'city':  # Skip city column as we'll add it in the desired position
            # Preserve the original nullable status and default values of each column
            nullable_str = " NOT NULL" if not col['nullable'] else ""
            
            # Handle default values, including NULL defaults
            if col['default'] is not None:
                default_str = f" DEFAULT {col['default']}"
            elif col['nullable']:
                default_str = " DEFAULT NULL"
            else:
                default_str = ""
                
            # Ensure location_link column allows NULLs
            if col['name'] == 'location_link':
                nullable_str = ""  # Allow NULLs for location_link
            
            column_definitions.append(
                f"{col['name']} {col['type']}{nullable_str}{default_str}"
            )
    
    # Get the nullable status of the city column from the original table
    city_column = next(col for col in columns if col['name'] == 'city')
    city_nullable_str = " NOT NULL" if not city_column['nullable'] else ""
    
    # Join all column definitions and create the new table
    columns_sql = ",\n".join([
        *[cd for cd in column_definitions[:3]],  # columns before city
        f"city VARCHAR(255){city_nullable_str}",  # city column with original nullable status
        *[cd for cd in column_definitions[3:]]   # remaining columns
    ])
    op.execute(f"""
        CREATE TABLE restaurants_new (
            {columns_sql}
        )
    """)
    
    # Copy data
    op.execute("""
        INSERT INTO restaurants_new 
        SELECT * FROM restaurants
    """)
    
    # Drop old table and rename new one
    op.drop_table('restaurants')
    op.rename_table('restaurants_new', 'restaurants')

def downgrade():
    pass
