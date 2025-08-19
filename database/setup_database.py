#!/usr/bin/env python3
"""
Database setup script for MCP PostgreSQL client
Automatically creates schema, tables, and sample data
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path
from dotenv import load_dotenv

def read_sql_file(file_path):
    """Read SQL file content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def setup_database(database_uri):
    """Set up the database with schema and sample data"""
    try:
        # Connect to PostgreSQL
        print(f"Connecting to database...")
        conn = psycopg2.connect(database_uri)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Read and execute the setup SQL script
        script_path = Path(__file__).parent / "setup_schema.sql"
        if not script_path.exists():
            print(f"Error: SQL script not found at {script_path}")
            return False
            
        print("Reading SQL setup script...")
        sql_script = read_sql_file(script_path)
        
        print("Executing database setup...")
        cursor.execute(sql_script)
        
        # Verify the setup
        print("Verifying database setup...")
        cursor.execute("""
            SELECT 
                schemaname, 
                tablename, 
                tableowner 
            FROM pg_tables 
            WHERE schemaname = 'research_papers'
            ORDER BY tablename;
        """)
        
        tables = cursor.fetchall()
        print(f"Created {len(tables)} tables in research_papers schema:")
        for table in tables:
            print(f"  - {table[1]}")
        
        # Check sample data
        cursor.execute("SELECT COUNT(*) FROM research_papers.ai_research_papers;")
        paper_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM research_papers.research_topics;")
        topic_count = cursor.fetchone()[0]
        
        print(f"Sample data inserted:")
        print(f"  - {paper_count} research papers")
        print(f"  - {topic_count} research topics")
        
        cursor.close()
        conn.close()
        
        print("✅ Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def main():
    """Main function"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get database URI from environment variable or use default
    database_uri = os.getenv("DATABASE_URI", "postgresql://user:password@localhost:5432/dbname")
    
    if not database_uri:
        print("❌ Error: DATABASE_URI environment variable is required")
        print("Please set it in your .env file or as an environment variable")
        sys.exit(1)
    
    print("🚀 Setting up PostgreSQL database for MCP client...")
    print(f"Database URI: {database_uri.replace('password', '***') if 'password' in database_uri else database_uri}")
    
    success = setup_database(database_uri)
    
    if success:
        print("\n🎉 Database is ready for use with the MCP PostgreSQL client!")
        print("\nNext steps:")
        print("1. Start the PostgreSQL MCP server:")
        print(f"   export DATABASE_URI='{database_uri}'")
        print("   postgres-mcp --access-mode=unrestricted --transport=sse")
        print("2. Run the MCP client:")
        print("   cd pg && python main.py")
    else:
        print("\n❌ Database setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
