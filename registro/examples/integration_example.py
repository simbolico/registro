"""
# Registro FastAPI Integration Example
# ==================================

## Overview
This example demonstrates how to integrate Registro with FastAPI to build a robust
RESTful API with resource-centric design. It shows how Registro's resource identification
and management capabilities enhance web API development by providing consistent 
resource handling, validation, and relationship management.

## What This Example Covers
1. Integrating Registro with FastAPI for building REST APIs
2. Creating a simple task management API with CRUD operations
3. Using Pydantic schemas for request and response models
4. Implementing resource-based API endpoints
5. Leveraging Registro's resource identification and metadata

## Key Concepts
- **ResourceBase Integration**: Using Registro models in FastAPI endpoints
- **Pydantic Integration**: Converting between Registro models and API schemas
- **RESTful Endpoints**: Building resource-oriented API endpoints
- **Resource Querying**: Filtering and retrieving resources in API context
- **Resource Relationships**: Working with related resources in a web API
"""

import os
import sys

# Add parent directory to path so we can import registro
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uvicorn
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

from registro import ResourceBase, Resource
from registro.config import settings

"""
## Step 1: Configure Registro

First, we configure Registro with our service and instance names. These will be used
in the RIDs (Resource Identifiers) for all resources created by this application.

- service: Identifies the application domain ("task-manager")
- instance: Identifies the deployment environment ("demo")

This configuration allows for logical separation of resources in different services
and environments while maintaining a consistent identification pattern.
"""

# Configure Registro
settings.DEFAULT_SERVICE = "task-manager"  # The service name for all resources
settings.DEFAULT_INSTANCE = "demo"         # The instance name for all resources

"""
## Step 2: Set Up the Database

We'll set up a SQLite database for storing our resources. In a production environment,
you might use PostgreSQL, MySQL, or another database supported by SQLAlchemy.
"""

# Database setup
sqlite_file = "tasks.db"
if os.path.exists(sqlite_file):
    os.remove(sqlite_file)

engine = create_engine(f"sqlite:///{sqlite_file}")
SQLModel.metadata.create_all(engine)

"""
## Step 3: Create a Database Session Dependency

FastAPI uses dependency injection to provide components like database sessions.
This ensures proper session management and connection pooling.
"""

# Dependency to get database session
def get_session():
    """
    Create and yield a database session.
    
    This is a FastAPI dependency that creates a new SQLModel session for each 
    request and ensures it's properly closed afterward, even if exceptions occur.
    """
    with Session(engine) as session:
        yield session

"""
## Step 4: Define Resource Models

Next, we define our domain models by extending ResourceBase. This adds resource
capabilities to our models, including RIDs, status tracking, and metadata.

For our task manager, we'll create a Task model that represents a todo item.
"""

# Resource model
class Task(ResourceBase, table=True):
    """
    Task model with resource capabilities.
    
    Each task becomes a resource with a unique RID and is tracked in the 
    Resource registry. This model represents a todo item in our task manager.
    
    Attributes:
        title (str): The task title
        description (str, optional): Detailed description of the task
        completed (bool): Whether the task is completed
        priority (int): Task priority (1=low, 2=medium, 3=high)
        tags (str, optional): Comma-separated tags for categorization
    """
    __resource_type__ = "task"  # The resource type, used in the RID
    
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    completed: bool = Field(default=False)
    priority: int = Field(default=1)  # 1=low, 2=medium, 3=high
    tags: Optional[str] = Field(default=None)  # Comma-separated tags
    
    @property
    def tag_list(self) -> List[str]:
        """
        Convert tags string to list.
        
        This convenience property splits the comma-separated tags string
        into a list of individual tags, making it easier to work with tags
        in application code.
        
        Returns:
            List[str]: List of tags, or empty list if no tags
        """
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

"""
## Step 5: Define API Schemas

We'll use Pydantic models (via SQLModel) to define request and response schemas.
This provides:

1. Input validation for API requests
2. Response serialization
3. API documentation (via OpenAPI/Swagger)
4. Clear separation between database models and API contracts
"""

# Pydantic schemas for API
class TaskCreate(SQLModel):
    """
    Schema for creating a task.
    
    This defines the fields required to create a new task resource.
    It's used for validating POST requests to the /tasks/ endpoint.
    
    Attributes:
        api_name (str): Machine-readable name for the task
        title (str): Human-readable title for the task
        description (str, optional): Detailed description
        priority (int): Task priority (1=low, 2=medium, 3=high)
        tags (str, optional): Comma-separated tags
    """
    api_name: str
    title: str
    description: Optional[str] = None
    priority: int = 1
    tags: Optional[str] = None

class TaskUpdate(SQLModel):
    """
    Schema for updating a task.
    
    This defines the fields that can be updated on an existing task.
    All fields are optional, allowing partial updates.
    
    Attributes:
        title (str, optional): Human-readable title for the task
        description (str, optional): Detailed description
        completed (bool, optional): Completion status
        priority (int, optional): Task priority (1=low, 2=medium, 3=high)
        tags (str, optional): Comma-separated tags
    """
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[int] = None
    tags: Optional[str] = None

class TaskResponse(SQLModel):
    """
    Schema for task response.
    
    This defines the shape of task data returned by the API.
    It includes both task-specific fields and resource metadata.
    
    Attributes:
        rid (str): Resource identifier (RID)
        api_name (str): Machine-readable name
        title (str): Human-readable title
        description (str, optional): Detailed description
        completed (bool): Completion status
        priority (int): Task priority
        tags (str, optional): Comma-separated tags
        status (str): Resource status
        service (str): Resource service
        resource_type (str): Resource type
        resource_id (str): Resource ID (part of RID)
    """
    rid: str
    api_name: str
    title: str
    description: Optional[str] = None
    completed: bool
    priority: int
    tags: Optional[str] = None
    status: str
    service: str
    resource_type: str
    resource_id: str

"""
## Step 6: Create FastAPI Application

Now we'll create the FastAPI application with metadata and configure it for
our task management API.
"""

# Create FastAPI application
app = FastAPI(
    title="Task Manager API",
    description="Task management API using Registro for resource management",
    version="1.0.0"
)

"""
## Step 7: Implement API Endpoints

Next, we'll implement the API endpoints for our task manager. We'll follow
RESTful design principles with the following endpoints:

- GET /tasks/ - List all tasks (with optional filtering)
- POST /tasks/ - Create a new task
- GET /tasks/{task_rid} - Get a specific task by RID
- PUT /tasks/{task_rid} - Update a specific task
- DELETE /tasks/{task_rid} - Delete a specific task
- GET /resources/ - List all resources (with optional filtering)

Each endpoint demonstrates how to work with Registro resources in an API context.
"""

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint that returns API information.
    
    This provides basic information about the API, including metadata 
    about the Registro service and instance configuration.
    
    Returns:
        dict: API information
    """
    return {
        "message": "Task Manager API",
        "documentation": "/docs",
        "service": settings.DEFAULT_SERVICE,
        "instance": settings.DEFAULT_INSTANCE
    }

# Create a task
@app.post("/tasks/", response_model=TaskResponse)
async def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    """
    Create a new task.
    
    This endpoint creates a new task resource from the provided data.
    The task is automatically assigned a unique RID with the format:
    ri.task-manager.demo.task.{id}
    
    Parameters:
        task (TaskCreate): The task data from the request body
        session (Session): Database session (injected via dependency)
    
    Returns:
        TaskResponse: The created task with resource metadata
    """
    # Convert the Pydantic model to a database model
    db_task = Task(**task.model_dump())
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    
    # Convert to response model with resource metadata
    response_data = db_task.model_dump()
    response_data.update({
        "service": db_task.service,
        "resource_type": db_task.resource_type,
        "resource_id": db_task.resource_id,
    })
    
    return response_data

# Get all tasks
@app.get("/tasks/", response_model=List[TaskResponse])
async def read_tasks(
    completed: Optional[bool] = None,
    priority: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """
    Get all tasks with optional filtering.
    
    This endpoint retrieves all tasks, with optional filtering by completion
    status and priority level.
    
    Parameters:
        completed (bool, optional): Filter by completion status
        priority (int, optional): Filter by priority level
        session (Session): Database session (injected via dependency)
    
    Returns:
        List[TaskResponse]: List of tasks with resource metadata
    """
    query = select(Task)
    
    # Apply filters
    if completed is not None:
        query = query.where(Task.completed == completed)
    if priority is not None:
        query = query.where(Task.priority == priority)
    
    tasks = session.exec(query).all()
    
    # Enhance with resource data
    result = []
    for task in tasks:
        task_data = task.model_dump()
        task_data.update({
            "service": task.service,
            "resource_type": task.resource_type,
            "resource_id": task.resource_id,
        })
        result.append(task_data)
    
    return result

@app.get("/tasks/{task_rid}", response_model=TaskResponse)
async def read_task(task_rid: str, session: Session = Depends(get_session)):
    """
    Get a specific task by its RID.
    
    This endpoint retrieves a specific task by its Resource Identifier (RID).
    The RID uniquely identifies the task across the entire system.
    
    Parameters:
        task_rid (str): The Resource Identifier (RID) of the task
        session (Session): Database session (injected via dependency)
    
    Returns:
        TaskResponse: The task with resource metadata
    
    Raises:
        HTTPException: If the task is not found (404)
    """
    task = session.exec(select(Task).where(Task.rid == task_rid)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = task.model_dump()
    task_data.update({
        "service": task.service,
        "resource_type": task.resource_type,
        "resource_id": task.resource_id,
    })
    
    return task_data

@app.put("/tasks/{task_rid}", response_model=TaskResponse)
async def update_task(
    task_rid: str,
    task_update: TaskUpdate,
    session: Session = Depends(get_session)
):
    """
    Update a task.
    
    This endpoint updates a specific task identified by its RID.
    Only the fields provided in the request will be updated.
    
    Parameters:
        task_rid (str): The Resource Identifier (RID) of the task
        task_update (TaskUpdate): The task data to update from request body
        session (Session): Database session (injected via dependency)
    
    Returns:
        TaskResponse: The updated task with resource metadata
    
    Raises:
        HTTPException: If the task is not found (404)
    """
    db_task = session.exec(select(Task).where(Task.rid == task_rid)).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update non-None fields
    task_data = task_update.model_dump(exclude_unset=True)
    for key, value in task_data.items():
        setattr(db_task, key, value)
    
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    
    response_data = db_task.model_dump()
    response_data.update({
        "service": db_task.service,
        "resource_type": db_task.resource_type,
        "resource_id": db_task.resource_id,
    })
    
    return response_data

@app.delete("/tasks/{task_rid}")
async def delete_task(task_rid: str, session: Session = Depends(get_session)):
    """
    Delete a task.
    
    This endpoint deletes a specific task identified by its RID.
    The task is permanently removed from the database.
    
    Parameters:
        task_rid (str): The Resource Identifier (RID) of the task
        session (Session): Database session (injected via dependency)
    
    Returns:
        dict: Message confirming deletion
    
    Raises:
        HTTPException: If the task is not found (404)
    """
    db_task = session.exec(select(Task).where(Task.rid == task_rid)).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    session.delete(db_task)
    session.commit()
    
    return {"message": "Task deleted successfully"}

@app.get("/resources/", response_model=List[Dict[str, Any]])
async def read_resources(
    resource_type: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Get all resources with optional filtering.
    
    This endpoint demonstrates how to work directly with the Resource registry.
    It retrieves all resources or filters them by resource type.
    
    Parameters:
        resource_type (str, optional): Filter by resource type
        session (Session): Database session (injected via dependency)
    
    Returns:
        List[Dict[str, Any]]: List of resources with metadata
    """
    query = select(Resource)
    
    # Apply filters
    if resource_type:
        query = query.where(Resource.resource_type == resource_type)
    
    resources = session.exec(query).all()
    
    return [
        {
            "rid": r.rid,
            "id": r.id,
            "service": r.service,
            "instance": r.instance,
            "resource_type": r.resource_type,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in resources
    ]

"""
## Best Practices for API Design with Registro

1. **Resource-Oriented Design**: 
   - Use RIDs for consistent resource identification
   - Structure endpoints around resources
   - Define clear resource boundaries

2. **Schema Separation**:
   - Separate database models (ResourceBase) from API schemas
   - Use validation in request models
   - Include resource metadata in response models

3. **Consistent Response Patterns**:
   - Always include RIDs in responses
   - Provide useful resource metadata
   - Use consistent error patterns

4. **Resource Relationships**:
   - Use RIDs to reference related resources
   - Implement relationship endpoints when needed
   - Consider pagination for relationship collections

5. **Resource Discovery**:
   - Provide endpoints for discovering resources
   - Support filtering by resource attributes
   - Consider hypermedia links for navigation
"""

# Run the application if executed directly
if __name__ == "__main__":
    print("Starting Task Manager API with Registro...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
    # To run this example:
    # python integration_example.py
    #
    # Then visit:
    # - API docs: http://127.0.0.1:8000/docs
    # - Create a task: POST http://127.0.0.1:8000/tasks/
    # - List tasks: GET http://127.0.0.1:8000/tasks/
    # - Get resources: GET http://127.0.0.1:8000/resources/
