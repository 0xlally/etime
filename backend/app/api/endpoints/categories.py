"""Category Endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new category for the current user.
    
    Args:
        category_data: Category creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created category
        
    Raises:
        HTTPException: If category name already exists for this user
    """
    # Check if category name already exists for this user
    existing = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.name == category_data.name,
        Category.is_archived == False  # Only check non-archived
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category_data.name}' already exists"
        )
    
    # Create new category
    new_category = Category(
        user_id=current_user.id,
        name=category_data.name,
        color=category_data.color
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category


@router.get("", response_model=List[CategoryResponse])
def list_categories(
    include_archived: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all categories for the current user.
    
    Args:
        include_archived: Whether to include archived categories
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of user's categories
    """
    query = db.query(Category).filter(Category.user_id == current_user.id)
    
    if not include_archived:
        query = query.filter(Category.is_archived == False)
    
    categories = query.order_by(Category.created_at.desc()).all()
    return categories


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific category by ID.
    
    Args:
        category_id: Category ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Category details
        
    Raises:
        HTTPException: If category not found or doesn't belong to user
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Verify ownership
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this category"
        )
    
    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a category.
    
    Args:
        category_id: Category ID
        category_data: Category update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated category
        
    Raises:
        HTTPException: If category not found, doesn't belong to user, or name conflict
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Verify ownership
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this category"
        )
    
    # Check name uniqueness if name is being updated
    if category_data.name and category_data.name != category.name:
        existing = db.query(Category).filter(
            Category.user_id == current_user.id,
            Category.name == category_data.name,
            Category.id != category_id,
            Category.is_archived == False
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_data.name}' already exists"
            )
    
    # Update fields
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    hard_delete: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete (archive) a category.
    
    By default, performs soft delete (sets is_archived=True).
    Use hard_delete=True to permanently delete.
    
    Args:
        category_id: Category ID
        hard_delete: If True, permanently delete; if False, soft delete (archive)
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If category not found or doesn't belong to user
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Verify ownership
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this category"
        )
    
    if hard_delete:
        # Permanent delete
        db.delete(category)
    else:
        # Soft delete (archive)
        category.is_archived = True
    
    db.commit()
    return None
