"""
# Registro Integration Example
# ===========================

## Overview
This example demonstrates how to integrate Registro with FastAPI to create a
complete API for managing resources. It shows best practices for:

1. Defining resource models with Registro
2. Exposing resources via FastAPI endpoints
3. Handling database sessions and relationships
4. Separating database models from API schemas
5. Using enhanced ResourceTypeBaseModel features

## Key Concepts
- **FastAPI Integration**: Exposing Registro resources in web APIs
- **ResourceTypeBaseModel Integration**: Using Registro models in FastAPI endpoints
- **Pydantic Schemas**: Creating API schemas from Registro models
- **CRUD Operations**: Complete Create, Read, Update, Delete API
- **Enhanced Features**: Using relationship helpers and to_dict serialization
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add the base workspace directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
workspace_dir = parent_dir.parent
sys.path.insert(0, str(workspace_dir))

from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse

try:
    from registro import ResourceTypeBaseModel
    from registro.config import settings
except ImportError:
    # Alternative imports if running from examples directory
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from registro import ResourceTypeBaseModel
    from registro.config import settings

# Configure Registro settings
settings.DEFAULT_SERVICE = "task-manager"
settings.DEFAULT_INSTANCE = "demo"

# Create a SQLite database
sqlite_file = "tasks.db"
if os.path.exists(sqlite_file):
    os.remove(sqlite_file)

# Create engine and database
engine = create_engine(f"sqlite:///{sqlite_file}", echo=False)

# Define database dependency
def get_db():
    """Dependency to get a database session"""
    with Session(engine) as session:
        yield session

# Define the Task resource model using ResourceTypeBaseModel with enhanced features
class Task(ResourceTypeBaseModel, table=True):
    """
    Task model with resource capabilities.
    
    A task represents a unit of work in our task management system.
    Each task automatically becomes a resource with a unique RID.
    This example demonstrates enhanced ResourceTypeBaseModel features.
    """
    __resource_type__ = "task"
    
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    completed: bool = Field(default=False)
    priority: int = Field(default=1)  # 1=lowest, 5=highest
    
    # Relationship to project (could be added later)
    project_rid: Optional[str] = Field(default=None)
    project_api_name: Optional[str] = Field(default=None)
    
    def to_api_dict(self) -> Dict[str, Any]:
        """
        Convert to API-friendly dictionary using enhanced to_dict method.
        Demonstrates custom usage of the enhanced to_dict method.
        """
        # Use the enhanced to_dict method with exclusions
        data = self.to_dict(exclude={"project_rid"})
        
        # Add some computed fields
        data["is_high_priority"] = self.priority >= 4
        data["status_text"] = "Completed" if self.completed else "In Progress"
        
        return data

# Add a method to get task by api_name using enhanced get_related_resource
def get_task_by_api_name(api_name: str, session: Session) -> Optional[Task]:
    """
    Get a task by its API name using the enhanced get_related_resource method.
    This demonstrates using the helper method statically.
    
    Args:
        api_name: The API name to search for
        session: SQLModel session
        
    Returns:
        The found task or None
    """
    # Create a dummy task to use its methods
    dummy = Task(api_name="dummy")
    return dummy.get_related_resource(
        model_class=Task,
        api_name=api_name,
        session=session
    )

# Create the database tables
SQLModel.metadata.create_all(engine)

# Create FastAPI app
app = FastAPI(
    title="Registro Task Manager",
    description="API for managing tasks using Registro resource framework",
    version="1.0.0"
)

# Define API schemas for input/output

class TaskCreate(SQLModel):
    """Schema for creating a task"""
    api_name: str
    display_name: str
    title: str
    description: Optional[str] = None
    priority: int = 1
    completed: bool = False
    
class TaskRead(SQLModel):
    """Schema for reading a task"""
    rid: str
    api_name: str
    display_name: str
    title: str
    description: Optional[str] = None
    priority: int
    completed: bool
    status: str
    
class TaskUpdate(SQLModel):
    """Schema for updating a task"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    completed: Optional[bool] = None
    status: Optional[str] = None
    display_name: Optional[str] = None

# Define API endpoints

@app.post("/tasks/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=List[TaskRead])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all tasks"""
    tasks = db.exec(select(Task).offset(skip).limit(limit)).all()
    return tasks

@app.get("/tasks/{task_rid}", response_model=TaskRead)
def read_task(task_rid: str, db: Session = Depends(get_db)):
    """Get a specific task by RID"""
    task = db.exec(select(Task).where(Task.rid == task_rid)).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/tasks/{task_rid}", response_model=TaskRead)
def update_task(task_rid: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task"""
    task = db.exec(select(Task).where(Task.rid == task_rid)).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update the task with the provided fields
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_rid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_rid: str, db: Session = Depends(get_db)):
    """Delete a task"""
    task = db.exec(select(Task).where(Task.rid == task_rid)).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return None

@app.post("/tasks/{task_rid}/toggle", response_model=TaskRead)
def toggle_task_status(task_rid: str, db: Session = Depends(get_db)):
    """Toggle task completion status"""
    task = db.exec(select(Task).where(Task.rid == task_rid)).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Toggle the completed status
    task.completed = not task.completed
    
    # Update the status based on completion
    if task.completed:
        task.status = "ACTIVE"
    else:
        task.status = "DRAFT"
    
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.get("/tasks/api/{api_name}", response_model=TaskRead)
def read_task_by_api_name(api_name: str, db: Session = Depends(get_db)):
    """Get a specific task by API name using the enhanced helper method"""
    task = get_task_by_api_name(api_name, db)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# Add a to_dict endpoint to demonstrate the enhanced serialization
@app.get("/tasks/{task_rid}/dict")
def get_task_dict(task_rid: str, db: Session = Depends(get_db)):
    """Get a task's dictionary representation using the enhanced to_dict method"""
    task = db.exec(select(Task).where(Task.rid == task_rid)).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Use the custom to_api_dict method that builds on enhanced to_dict
    return JSONResponse(content=task.to_api_dict())

# Add root endpoint for API information
@app.get("/")
def read_root():
    """Get API information"""
    return {
        "title": "Registro Task Manager",
        "description": "API for managing tasks using Registro resource framework",
        "version": "1.0.0",
        "documentation": "/docs",
        "service": settings.DEFAULT_SERVICE,
        "instance": settings.DEFAULT_INSTANCE
    }

# Instructions for running the API
if __name__ == "__main__":
    print("Task Manager API initialized.")
    print("To run the API, execute:")
    print("   uvicorn registro.examples.integration_example:app --reload")
    print("\nTo view API documentation:")
    print("   http://localhost:8000/docs")
