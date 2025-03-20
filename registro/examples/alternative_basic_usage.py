"""
# Registro Alternative Basic Usage Example
# =======================================

## Overview
This example demonstrates the fundamental concepts of using Registro for managing resources
in a simple application. It shows how to create, query, and manage resources with minimal
setup, perfect for getting started with the library.

## What This Example Covers
1. Creating a simple domain model with BaseResourceType (direct approach)
2. Configuring the service name
3. Creating database tables and storing resources
4. Querying resources by various attributes
5. Accessing resource metadata and relationships

## Key Concepts
- **BaseResourceType**: The foundation class that adds resource capabilities to your models
- **RIDs (Resource Identifiers)**: Unique identifiers with a structured format
- **Resource Registry**: Automatic tracking of all resources in a central registry
- **Resource Metadata**: Service, instance, type, and other metadata accessible via properties
"""

import os
import sys
from pathlib import Path

# Add the base workspace directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
workspace_dir = parent_dir.parent
sys.path.insert(0, str(workspace_dir))

from sqlmodel import Field, Session, SQLModel, create_engine, select
from registro import BaseResourceType, Resource
from registro.config import settings

"""
## Step 1: Configure Registro

First, we need to configure Registro with our service name. This will be used as part of the
RID (Resource Identifier) for all resources. The service name typically represents your
application or domain.

You can also configure this via environment variables:
- REGISTRO_DEFAULT_SERVICE
- REGISTRO_DEFAULT_INSTANCE
"""

# Configure the service name - this will be used in all RIDs
settings.DEFAULT_SERVICE = "bookshop"
settings.DEFAULT_INSTANCE = "demo"

"""
## Step 2: Define Resource Models

Next, we define our domain models using BaseResourceType. This adds 
resource capabilities to our models, including:

- Unique RIDs with format: ri.{service}.{instance}.{resource_type}.{id}
- Status tracking
- Automatic registration in the Resource registry
- Metadata properties (service, instance, resource_type, etc.)
"""

# Define a Book model
class Book(BaseResourceType, table=True):
    """
    Book model with resource capabilities.
    
    This model represents books in our bookshop system. Each book automatically
    becomes a resource with a unique RID when created.
    
    Attributes:
        title (str): The book title
        author (str): The book author
        year (int): Publication year
        pages (int): Number of pages
    """
    # Define the resource type - this becomes part of the RID
    __resource_type__ = "book"
    
    # Define model fields
    title: str = Field(index=True)
    author: str = Field(index=True)
    year: int = Field(default=2023)
    pages: int = Field(default=0)
    
    def __repr__(self):
        """String representation of a Book."""
        return f"Book(rid={self.rid}, title='{self.title}', author='{self.author}')"

"""
## Step 3: Set Up the Database

Now we'll set up a SQLite database for storing our resources. Registro works with
SQLModel, which is built on SQLAlchemy, providing a powerful yet easy-to-use ORM.
"""

# Create a SQLite database
sqlite_file = "bookshop_alt.db"
if os.path.exists(sqlite_file):
    os.remove(sqlite_file)

engine = create_engine(f"sqlite:///{sqlite_file}", echo=False)  # Set to False to reduce output
SQLModel.metadata.create_all(engine)

"""
## Step 4: Create and Save Resources

Let's create some book resources and save them to the database. When we create
instances of our Book model, they automatically become resources with unique RIDs.
"""

# Create and save books
with Session(engine) as session:
    # Create books - resources are created automatically
    books = [
        Book(
            api_name=f"book{i}",          # Machine-readable identifier
            display_name=f"Book {i}",      # Human-readable name 
            title=f"Book {i}",            # Book title 
            author=f"Author {i}",         # Author name
            year=2020 + i,                # Publication year
            pages=100 + i * 50            # Number of pages
        )
        for i in range(1, 6)
    ]
    
    # Add books to the session and commit
    for book in books:
        session.add(book)
    session.commit()
    
    # Refresh to get generated values and print details
    for book in books:
        session.refresh(book)
        print(f"Created: {book}")
        print(f"  RID: {book.rid}")  # Resource Identifier with format ri.{service}.{instance}.{resource_type}.{id}
        print(f"  Service: {book.service}")  # The service name (from RID)
        print(f"  Resource Type: {book.resource_type}")  # The resource type (from RID)
        print()

"""
## Step 5: Query Resources

Now that we have created some resources, let's query them in various ways.
Registro works seamlessly with SQLModel queries.
"""

# Query books
with Session(engine) as session:
    # Query by API name
    book = session.exec(select(Book).where(Book.api_name == "book1")).first()
    print(f"Found book by API name: {book}")
    
    # Query by title
    book = session.exec(select(Book).where(Book.title == "Book 3")).first()
    print(f"Found book by title: {book}")
    
    # Get the Resource record from the Book instance
    if book:
        resource = book.get_resource(session)
        print(f"Associated Resource: {resource.rid} (created at {resource.created_at})")
    
    # Query for all books with year > 2022
    books = session.exec(select(Book).where(Book.year > 2022)).all()
    print(f"\nBooks published after 2022:")
    for book in books:
        print(f"  {book.title} ({book.year}) - {book.rid}")

"""
## Step 6: Work with Resource Relationships

Registro maintains a registry of all resources in the central Resource table.
This allows us to query resources independently of their specific types, and
join with type-specific tables when needed.
"""

# Use resource relationships
with Session(engine) as session:
    # Query directly from Resource table
    resources = session.exec(
        select(Resource).where(Resource.resource_type == "book")
    ).all()
    
    print(f"\nFound {len(resources)} book resources:")
    for resource in resources:
        print(f"  {resource.rid} (created at {resource.created_at})")
    
    # Join with Book table - this demonstrates how to work with both tables
    book_resources = session.exec(
        select(Book, Resource).
        join(Resource, Book.rid == Resource.rid).
        where(Resource.service == "bookshop")
    ).all()
    
    print(f"\nBooks with their resources:")
    for book, resource in book_resources:
        print(f"  {book.title} - {resource.rid}")

"""
## Key Takeaways

1. **BaseResourceType Inheritance**: This example shows the direct inheritance approach
2. **Unique Identifiers**: RIDs provide globally unique identifiers with built-in metadata
3. **Automatic Registration**: Resources are automatically tracked in the registry
4. **Metadata Access**: Access service, instance, and type information directly
5. **Query Flexibility**: Query by model attributes or resource properties

## Next Steps

- Compare this with the decorator approach in basic_usage.py
- Check out custom_resource.py for custom status values and validators
- See integration_example.py for using Registro with FastAPI
"""

print("\nAlternative basic usage example completed successfully!") 