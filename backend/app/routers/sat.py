"""SAT catalog codes API (ticket 04).

Lists active ClaveProdServ and ClaveUnidad codes. Admin CRUD can be added later.
"""

from fastapi import APIRouter, Depends

from ..auth import get_db_conn, require_user
from ..services.sat_catalogs import list_product_codes, list_unit_codes

router = APIRouter(prefix="/api/sat", tags=["sat"])


@router.get("/product-codes")
def get_product_codes(conn=Depends(get_db_conn), user=Depends(require_user)):
    return list_product_codes(conn, active_only=True)


@router.get("/unit-codes")
def get_unit_codes(conn=Depends(get_db_conn), user=Depends(require_user)):
    return list_unit_codes(conn, active_only=True)
