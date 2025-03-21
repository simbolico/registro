#!/usr/bin/env python3
"""
Test script for enhanced ResourceTypeBaseModel features.
"""

from registro import ResourceTypeBaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select
from registro.config import settings
from typing import Optional

# Define a test model
class Department(ResourceTypeBaseModel, table=True):
    """Test department model."""
    __resource_type__ = "department"
    
    name: str = Field(...)
    code: str = Field(...)
    
    @classmethod
    def validate_department_code(cls, value: str) -> str:
        """Validate department code using validate_identifier."""
        return cls.validate_identifier(value, "Department code")

class Employee(ResourceTypeBaseModel, table=True):
    """Test employee model with relationship to department."""
    __resource_type__ = "employee"
    
    name: str = Field(...)
    department_rid: Optional[str] = Field(default=None, foreign_key="department.rid")
    department_api_name: Optional[str] = Field(default=None)
    
    def link_to_department(self, session: Session, dept_api_name: str) -> "Department":
        """Link to department using link_resource helper."""
        return self.link_resource(
            session=session,
            model_class=Department,
            rid_field="department_rid",
            api_name_field="department_api_name",
            api_name_value=dept_api_name
        )

def main():
    """Main test function."""
    print("Testing enhanced ResourceTypeBaseModel features...")
    
    # Setup in-memory database
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    # Test initialization with service/instance
    with Session(engine) as session:
        # Test service/instance initialization
        dept = Department(
            service="test-service",
            instance="test-instance",
            api_name="engineering",
            display_name="Engineering Department",
            name="Engineering",
            code="eng_dept"
        )
        
        session.add(dept)
        session.commit()
        
        print(f"Department created:")
        print(f"  Service: {dept.service}")
        print(f"  Instance: {dept.instance}")
        print(f"  RID: {dept.rid}")
        
        # Test to_dict
        dept_dict = dept.to_dict()
        print("\nDepartment to_dict output:")
        print(f"  API Name: {dept_dict['api_name']}")
        print(f"  Service: {dept_dict['service']}")
        print(f"  Resource Type: {dept_dict['resource_type']}")
        
        # Test relationship helpers
        employee = Employee(
            api_name="john-doe",
            display_name="John Doe",
            name="John Doe"
        )
        
        # Link to department
        print("\nLinking employee to department...")
        employee.link_to_department(session, "engineering")
        
        print(f"  Employee department_rid: {employee.department_rid}")
        print(f"  Employee department_api_name: {employee.department_api_name}")
        
        session.add(employee)
        session.commit()
        
        # Test get_related_resource
        retrieved_dept = employee.get_related_resource(
            Department,
            api_name="engineering",
            session=session
        )
        
        if retrieved_dept:
            print("\nRetrieved department using get_related_resource:")
            print(f"  Name: {retrieved_dept.name}")
            print(f"  Code: {retrieved_dept.code}")
        
        # Test validation
        try:
            print("\nTesting field validation...")
            Department.validate_department_code("valid_code")
            print("  Valid code passed validation")
            
            Department.validate_department_code("invalid-code")
            print("  FAILED: Invalid code passed validation")
        except ValueError as e:
            print(f"  Validation error caught: {e}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 