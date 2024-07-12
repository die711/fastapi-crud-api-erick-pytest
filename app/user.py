import app.schemas as schemas
import app.models as models
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import Depends, HTTPException, status, APIRouter
from app.database import get_db

router = APIRouter()


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def create_user(payload: schemas.UserBaseSchema, db: Session = Depends(get_db)):
    try:
        # Create a new user instance from the payload
        new_user = models.User(**payload.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError as e:
        print('error', e)
        db.rollback()

        # Log the error on handle it as needed
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='A user with the given details already exists.'
        ) from e
    except Exception as e:
        print('error', e)
        db.rollback()
        # Handle other types of database errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='An error ocurred while creating the user'
        ) from e

    # Convert the SQLALCHEMY model instance to a pydantic model
    user_schema = schemas.UserBaseSchema.from_orm(new_user)
    # Return the successful creation  response
    return schemas.UserResponse(status=schemas.Status.Success, user=user_schema)


@router.get('/', status_code=status.HTTP_200_OK, response_model=schemas.ListUserResponse)
def get_users(db: Session = Depends(get_db), limit: int = 10, page: int = 1, search: str = ""):
    skip = (page - 1) * limit

    users = db.query(models.User).filter(models.User.first_name.contains(search)).limit(limit).offset(skip).all()

    return schemas.ListUserResponse(
        status=schemas.Status.Success, results=len(users), users=users
    )


@router.get('/{id}', status_code=status.HTTP_200_OK)
def get_user(id: str, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.id == id)
    db_user = user_query.first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'No User with this id: {id} found'
        )

    try:
        user = schemas.UserBaseSchema.model_validate(db_user)
        return schemas.UserResponse(status=schemas.Status.Success, user=user)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # detail=f'{e}'
            detail='An unexpected error occurred while fetching the user.'
        ) from e


@router.patch('/{id}', status_code=status.HTTP_202_ACCEPTED, response_model=schemas.UserResponse)
def update_user(id: str, payload: schemas.UserBaseSchema, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.id == id)
    db_user = user_query.first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'No User with this id: {id} found'
        )

    try:
        update_data = payload.dict(exclude_unset=True)
        print(update_data)
        user_query.update(update_data, synchronize_session=False)
        db.commit()
        db.refresh(db_user)
        user_schema = schemas.UserBaseSchema.model_validate(db_user)
        return schemas.UserResponse(status=schemas.Status.Success, user=user_schema)

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='A user with the given details already exists'
        ) from e

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='A user with the given details already exists'
        )


@router.delete("/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.DeleteUserResponse)
def delete_user(id: str, db: Session = Depends(get_db)):
    try:
        user_query = db.query(models.User).filter(models.User.id == id)
        user = user_query.first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='An error ocurred while deleting the user'
            )

        user_query.delete(synchronize_session=False)
        db.commit()
        return schemas.DeleteUserResponse(
            status=schemas.Status.Success,
            message='User deleted successfully'
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='An error ocurred while deleting the user.'
        ) from e
