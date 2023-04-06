from fastapi import APIRouter, Path, Depends, HTTPException, status
from fastapi_pagination import Page, paginate

from database import get_database, Links, Items
from models import Item


lamoda_router = APIRouter()


@lamoda_router.get("/lamoda")
async def root(database=Depends(get_database)) -> dict:

    buyer_type = Links.find().distinct('buyer_type')
    return {'buyer_type': buyer_type}


@lamoda_router.get("/lamoda/{buyer_type}")
async def get_categories(buyer_type: str = Path(..., title="Parent buyer type of these categories"),
                         database=Depends(get_database)) -> dict:

    categories = Links.find({'buyer_type': buyer_type}).distinct('category')

    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category does not exist",
        )

    return {'categories': categories}


@lamoda_router.get("/lamoda/{buyer_type}/{category}")
async def get_subcategories(buyer_type: str = Path(..., title="Parent buyer type of these categories"),
                            category: str = Path(..., title="Parent category of subcategories"),
                            database=Depends(get_database)) -> dict:

    sub_categories = Links.find({'buyer_type': buyer_type, 'category': category}).distinct('subcategory')

    if not sub_categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory does not exist",
        )

    return {'sub_categories': sub_categories}


@lamoda_router.get("/lamoda/{buyer_type}/{category}/{subcategory}", response_model=Page[Item])
async def get_items(buyer_type: str = Path(..., title="Parent buyer type of these categories"),
                    category: str = Path(..., title="Parent category of subcategories"),
                    subcategory: str = Path(..., title="Parent subcategory of item types"),
                    database=Depends(get_database)) -> dict:

    subcategory = Links.find_one({'buyer_type': buyer_type, 'category': category, 'subcategory': subcategory})
    items = list(Items.find({'category_url': subcategory['url_string']}))
    return paginate(items)
