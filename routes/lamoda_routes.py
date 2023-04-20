from time import sleep

from fastapi import APIRouter, Path, Depends, HTTPException, status
from fastapi_pagination import Page, paginate


from database import ItemsDatabase, CatalogDatabase
from models import Item

from fastapi_cache.decorator import cache


lamoda_router = APIRouter()


@lamoda_router.get("/lamoda")
@cache(expire=60)
async def root(links_db=Depends(CatalogDatabase)) -> dict:
    buyer_type = links_db.get_all().distinct('buyer_type')
    return {'buyer_type': buyer_type}


@lamoda_router.get("/lamoda/{buyer_type}")
@cache(expire=60)
async def get_categories(buyer_type: str = Path(..., title="Parent buyer type of these categories"),
                         links_db=Depends(CatalogDatabase)) -> dict:

    categories = links_db.filter(buyer_type=buyer_type).distinct('category')

    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category does not exist",
        )

    return {'categories': categories}


@lamoda_router.get("/lamoda/{buyer_type}/{category}")
@cache(expire=60)
async def get_subcategories(buyer_type: str = Path(..., title="Parent buyer type of these categories"),
                            category: str = Path(..., title="Parent category of subcategories"),
                            links_db=Depends(CatalogDatabase)) -> dict:

    sub_categories = links_db.filter(buyer_type=buyer_type, category=category).distinct('subcategory')

    if not sub_categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory does not exist",
        )

    return {'sub_categories': sub_categories}


@lamoda_router.get("/lamoda/{buyer_type}/{category}/{subcategory}", response_model=Page[Item])
@cache(expire=60)
async def get_items(buyer_type: str = Path(..., title="Parent buyer type of these categories"),
                    category: str = Path(..., title="Parent category of subcategories"),
                    subcategory: str = Path(..., title="Parent subcategory of item types"),
                    links_db=Depends(CatalogDatabase),
                    items_db=Depends(ItemsDatabase)) -> dict:

    subcategory = links_db.get(buyer_type=buyer_type, category=category, subcategory=subcategory)

    if not subcategory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory does not exist",
        )
    items = list(items_db.filter(category_url=subcategory['url_string']))
    return paginate(items)


@lamoda_router.get("/test_cache")
@cache(expire=60)
async def test_cache():
    sleep(10)
    return {'answer': 'is it fast?'}