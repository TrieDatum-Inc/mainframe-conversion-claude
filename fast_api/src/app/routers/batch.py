"""Batch processing API routes.

Maps COBOL batch JCL jobs to REST endpoints:
  POST /api/batch/transaction-posting -> CBTRN02C
  POST /api/batch/transaction-report  -> CBTRN03C
  POST /api/batch/interest-calculation -> CBACT04C
  GET  /api/batch/export              -> CBEXPORT
  POST /api/batch/import              -> CBIMPORT
  GET  /api/batch/jobs/{job_id}       -> Job status
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.batch_job import BatchJobRepository
from app.schemas.batch import (
    BatchJobResponse,
    ExportResponse,
    ImportRequest,
    ImportResponse,
    InterestCalculationRequest,
    InterestCalculationResponse,
    TransactionPostingRequest,
    TransactionPostingResponse,
    TransactionReportRequest,
    TransactionReportResponse,
)
from app.services.export_import import ExportImportService
from app.services.interest_calculator import InterestCalculatorService
from app.services.transaction_posting import TransactionPostingService
from app.services.transaction_report import TransactionReportService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/batch", tags=["Batch Processing"])


@router.post(
    "/transaction-posting",
    response_model=TransactionPostingResponse,
    status_code=status.HTTP_200_OK,
    summary="CBTRN02C: Validate and post daily transactions",
    description=(
        "Validates each transaction in the request against cross-reference and account data. "
        "Valid transactions are posted to the transactions table. "
        "Invalid transactions are written to the daily_rejects table with reason codes. "
        "Returns HTTP 200 even when rejects occur (has_rejects=True maps to COBOL RETURN-CODE 4)."
    ),
)
async def post_transactions(
    request: TransactionPostingRequest,
    db: AsyncSession = Depends(get_db),
) -> TransactionPostingResponse:
    """CBTRN02C equivalent: validate and post daily transactions."""
    if not request.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transactions provided",
        )

    service = TransactionPostingService(db)
    try:
        result = await service.run(request.transactions)
        return TransactionPostingResponse(**result)
    except Exception as e:
        logger.exception("Transaction posting failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction posting failed: {e!s}",
        ) from e


@router.post(
    "/transaction-report",
    response_model=TransactionReportResponse,
    status_code=status.HTTP_200_OK,
    summary="CBTRN03C: Generate transaction detail report",
    description=(
        "Reads all transactions within the specified date range and generates "
        "a formatted report with account break subtotals and grand totals. "
        "Missing reference data (type/category) is logged as a warning instead of aborting "
        "(replaces COBOL ABEND behavior). "
        "Page size is 20 lines per CBTRN03C WS-PAGE-SIZE setting."
    ),
)
async def generate_transaction_report(
    request: TransactionReportRequest,
    db: AsyncSession = Depends(get_db),
) -> TransactionReportResponse:
    """CBTRN03C equivalent: generate transaction detail report."""
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be on or before end_date",
        )

    service = TransactionReportService(db)
    try:
        result = await service.run(request.start_date, request.end_date)
        return TransactionReportResponse(**result)
    except Exception as e:
        logger.exception("Transaction report generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {e!s}",
        ) from e


@router.post(
    "/interest-calculation",
    response_model=InterestCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="CBACT04C: Calculate and post monthly interest charges",
    description=(
        "Calculates monthly interest for all accounts based on transaction category balances. "
        "Formula: (balance * annual_rate) / 1200. "
        "Falls back to DEFAULT disclosure group when specific group rate not found. "
        "Creates interest transaction records and updates account current balances. "
        "Zeroes cycle credit/debit after posting (end-of-cycle operation). "
        "NOTE: Fee calculation (1400-COMPUTE-FEES) is not implemented per COBOL spec."
    ),
)
async def calculate_interest(
    request: InterestCalculationRequest,
    db: AsyncSession = Depends(get_db),
) -> InterestCalculationResponse:
    """CBACT04C equivalent: calculate and post monthly interest."""
    service = InterestCalculatorService(db)
    try:
        result = await service.run(request.run_date)
        return InterestCalculationResponse(**result)
    except Exception as e:
        logger.exception("Interest calculation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interest calculation failed: {e!s}",
        ) from e


@router.get(
    "/export",
    response_model=ExportResponse,
    status_code=status.HTTP_200_OK,
    summary="CBEXPORT: Export all data as JSON",
    description=(
        "Reads all 5 entity tables (customers, accounts, xrefs, transactions, cards) "
        "and returns a structured JSON export payload. "
        "Replaces CBEXPORT 500-byte fixed-width multi-type file format. "
        "Processing order is preserved: C -> A -> X -> T -> D (per COBOL spec)."
    ),
)
async def export_data(db: AsyncSession = Depends(get_db)) -> ExportResponse:
    """CBEXPORT equivalent: export all data as JSON."""
    service = ExportImportService(db)
    try:
        result = await service.export_all()
        return ExportResponse(**result)
    except Exception as e:
        logger.exception("Data export failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data export failed: {e!s}",
        ) from e


@router.post(
    "/import",
    response_model=ImportResponse,
    status_code=status.HTTP_200_OK,
    summary="CBIMPORT: Import data from JSON export payload",
    description=(
        "Accepts a JSON export payload (from /export) and imports all records. "
        "Records are routed by type (C/A/X/T/D) to the appropriate tables. "
        "3000-VALIDATE-IMPORT (COBOL stub) is implemented with real validation: "
        "referential integrity checks, required field validation, status value validation. "
        "Import continues on validation errors; errors are reported in the response."
    ),
)
async def import_data(
    request: ImportRequest,
    db: AsyncSession = Depends(get_db),
) -> ImportResponse:
    """CBIMPORT equivalent: import data from JSON export payload."""
    service = ExportImportService(db)
    try:
        result = await service.import_data(request.payload)
        return ImportResponse(**result)
    except Exception as e:
        logger.exception("Data import failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data import failed: {e!s}",
        ) from e


@router.get(
    "/jobs/{job_id}",
    response_model=BatchJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get batch job status",
    description="Retrieve the status and results of a batch job by ID.",
)
async def get_job_status(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> BatchJobResponse:
    """Retrieve batch job status."""
    repo = BatchJobRepository(db)
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found",
        )
    return BatchJobResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        status=job.status,
        started_at=job.started_at,
        completed_at=job.completed_at,
        records_processed=job.records_processed,
        records_rejected=job.records_rejected,
        result_summary=job.result_summary,
        created_at=job.created_at,
    )
