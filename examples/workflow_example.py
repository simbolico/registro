#!/usr/bin/env python3
"""
Example demonstrating the development workflow and testing process.

This file shows how to:
1. Create a feature branch
2. Make changes with proper testing
3. Commit with conventional commit messages
4. Run quality checks
5. Prepare for release
"""

from registro.models.rid import RID, generate_ulid


def main():
    """Example usage of RID generation."""
    # Generate a ULID
    ulid = generate_ulid()
    print(f"Generated ULID: {ulid}")
    assert len(ulid) == 26
    assert isinstance(ulid, str)
    
    # Generate a full RID
    rid = RID.generate(
        service="examples",
        instance="demo",
        type_="workflow"
    )
    print(f"Generated RID: {rid}")
    assert rid.startswith("ri.examples.demo.workflow.")
    
    # Parse RID components
    components = RID(rid).components()
    print(f"RID components: {components}")
    assert components["service"] == "examples"
    assert components["instance"] == "demo"
    assert components["type"] == "workflow"
    
    return rid


if __name__ == "__main__":
    # Run the example
    rid = main()
    print("\nWorkflow example completed successfully!")
    print("This demonstrates a typical development workflow:")
    print("1. ✅ Code changes with proper type hints")
    print("2. ✅ Comprehensive testing")
    print("3. ✅ Ready for commit with conventional commit message")
    print("4. ✅ Will pass pre-commit hooks")
    print("5. ✅ Ready for merge and release")
