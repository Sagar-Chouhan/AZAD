"""Centre and Batch CRUD routes."""
from fastapi import APIRouter, HTTPException
from typing import Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from models.centre import CentreCreate, BatchCreate, BatchAllocation

router = APIRouter(prefix="/api", tags=["Centres & Batches"])


@router.get("/centres")
def list_centres(page: int = 1, limit: int = 10):
    offset = (page - 1) * limit
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM central_centres")
        total = cur.fetchone()["total"]
        cur.execute("""
            SELECT c.id, c.centre_name as name, c.state_id, c.created_at,
                   s.state_name as state_name,
                   (SELECT COUNT(*) FROM flps f WHERE f.centre_id = c.id AND f.deleted_at IS NULL) as flp_count
            FROM central_centres c
            LEFT JOIN central_states s ON c.state_id = s.id
            ORDER BY c.centre_name
            LIMIT %s OFFSET %s
        """, (limit, offset))
        return {"total": total, "page": page, "limit": limit, "data": cur.fetchall()}

@router.post("/centres")
def create_centre(centre: CentreCreate):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO central_centres (centre_name, state_id) VALUES (%s, %s) RETURNING id, centre_name as name, state_id",
            (centre.name, centre.state_id)
        )
        return cur.fetchone()

@router.put("/centres/{centre_id}")
def update_centre(centre_id: int, centre: CentreCreate):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE central_centres SET centre_name = %s, state_id = %s WHERE id = %s RETURNING id, centre_name as name, state_id",
            (centre.name, centre.state_id, centre_id)
        )
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Centre not found")
        return result


@router.get("/batches")
def list_batches(centre_id: Optional[int] = None, centre_code: Optional[str] = None,
                 state_code: Optional[str] = None,
                 status: Optional[str] = None, page: int = 1, limit: int = 10):
    offset = (page - 1) * limit
    with get_cursor() as cur:
        conditions = []
        params = []
        if centre_id:
            conditions.append("b.centre_id = %s")
            params.append(centre_id)
        if status:
            conditions.append("b.status = %s")
            params.append(status)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        cur.execute(f"SELECT COUNT(*) as total FROM central_batches b{where}", params)
        total = cur.fetchone()["total"]
        cur.execute(f"""
            SELECT b.batch_id as id, b.batch_name as name, b.financial_year as year, b.centre_id, b.status, b.created_at,
                   (SELECT COUNT(*) FROM flps f WHERE f.batch_id = b.batch_id AND f.deleted_at IS NULL) as flp_count
            FROM central_batches b
            {where}
            ORDER BY b.financial_year DESC, b.batch_name
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        return {"total": total, "page": page, "limit": limit, "data": cur.fetchall()}

@router.get("/batches/{batch_id}")
def get_batch(batch_id: int):
    with get_cursor() as cur:
        cur.execute("""
            SELECT b.batch_id as id, b.batch_name as name, b.financial_year as year, b.centre_id, b.status, b.created_at,
                   (SELECT COUNT(*) FROM flps f WHERE f.batch_id = b.batch_id AND f.deleted_at IS NULL) as flp_count
            FROM central_batches b
            WHERE b.batch_id = %s
        """, (batch_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Batch not found")
        return result

@router.post("/batches")
def create_batch(batch: BatchCreate):
    with get_cursor() as cur:
        st = 1 if str(batch.status).lower() in ('1', 'active') else 0
        cur.execute(
            "INSERT INTO central_batches (batch_name, financial_year, centre_id, status) VALUES (%s, %s, %s, %s) RETURNING batch_id as id, batch_name as name, financial_year as year, centre_id, status",
            (batch.name, batch.year, batch.centre_id, st)
        )
        return cur.fetchone()

@router.put("/batches/{batch_id}")
def update_batch(batch_id: int, batch: BatchCreate):
    with get_cursor() as cur:
        cur.execute(
            "SELECT batch_id FROM central_batches WHERE batch_name = %s AND financial_year = %s AND batch_id != %s",
            (batch.name, batch.year, batch_id)
        )
        if cur.fetchone():
            raise HTTPException(status_code=400, detail=f"A batch with name '{batch.name}' for year '{batch.year}' already exists.")
        try:
            st = 1 if str(batch.status).lower() in ('1', 'active') else 0
            cur.execute(
                "UPDATE central_batches SET batch_name = %s, financial_year = %s, status = %s WHERE batch_id = %s RETURNING batch_id as id, batch_name as name, financial_year as year, centre_id, status",
                (batch.name, batch.year, st, batch_id)
            )
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Batch not found")
            return result
        except Exception as e:
            if 'duplicate key' in str(e).lower() or 'unique' in str(e).lower():
                raise HTTPException(status_code=400, detail=f"A batch with name '{batch.name}' for year '{batch.year}' already exists at this centre.")
            raise


@router.delete("/batches/{batch_id}")
def delete_batch(batch_id: int):
    """Delete a batch. Unlinks any rows in other tables that reference it
    so the hard DELETE doesn't trip a foreign-key violation.
    """
    with get_cursor() as cur:
        # Unlink FLPs from this batch
        cur.execute("UPDATE flps SET batch_id = NULL WHERE batch_id = %s", (batch_id,))
        cur.execute("UPDATE trainings SET batch_id = NULL WHERE batch_id = %s", (batch_id,))
        # Delete the batch
        cur.execute("DELETE FROM central_batches WHERE batch_id = %s RETURNING batch_id as id", (batch_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Batch not found")
    return {"message": "Batch deleted successfully"}


@router.get("/batches/{batch_id}/unallocated-flps")
def get_unallocated_flps(batch_id: int):
    """Return Active FLPs with no batch assignment in the same centre as this batch."""
    with get_cursor() as cur:
        cur.execute("SELECT centre_id FROM central_batches WHERE batch_id = %s", (batch_id,))
        batch = cur.fetchone()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        centre_id = batch.get("centre_id")

        if centre_id:
            cur.execute("""
                SELECT f.id, f.enrollment_number, f.name, f.mobile, f.status
                FROM flps f
                WHERE f.centre_id = %s
                  AND f.batch_id IS NULL
                  AND f.deleted_at IS NULL
                  AND f.status = 'Active'
                ORDER BY f.name
            """, (centre_id,))
            return {"data": cur.fetchall(), "centre_id": centre_id}
        return {"data": [], "centre_id": None}


@router.post("/batches/{batch_id}/allocate")
def allocate_flps_to_batch(batch_id: int, allocation: BatchAllocation):
    """Assign selected FLPs to this batch by setting their batch_id."""
    if not allocation.flp_ids:
        raise HTTPException(status_code=400, detail="No FLPs selected")
    with get_cursor() as cur:
        cur.execute("SELECT batch_id as id, centre_id FROM central_batches WHERE batch_id = %s", (batch_id,))
        batch = cur.fetchone()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        centre_id = batch.get("centre_id")
        updated = 0
        for flp_id in allocation.flp_ids:
            cur.execute("""
                UPDATE flps SET batch_id = %s
                WHERE id = %s
                  AND batch_id IS NULL
                  AND deleted_at IS NULL
                RETURNING id
            """, (batch_id, flp_id))
            if cur.fetchone():
                updated += 1
        return {"message": str(updated) + " FLP(s) allocated to batch", "allocated_count": updated}