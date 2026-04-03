"""
Unit tests for TransactionCreate / TransactionValidateRequest schemas.
Tests all COTRN02C VALIDATE-INPUT-DATA-FIELDS business rules.
"""

import pytest
from pydantic import ValidationError

from app.schemas.transaction import TransactionCreate, TransactionValidateRequest


VALID_PAYLOAD = {
    "card_num": "4111111111111111",
    "tran_type_cd": "01",
    "tran_cat_cd": "0001",
    "tran_source": "ONLINE",
    "tran_desc": "Test purchase",
    "tran_amt": "-00000052.47",
    "tran_orig_dt": "2026-03-01",
    "tran_proc_dt": "2026-03-01",
    "tran_merchant_id": "000000001",
    "tran_merchant_name": "Test Merchant",
    "tran_merchant_city": "New York",
    "tran_merchant_zip": "10001",
}


class TestKeyFieldValidation:
    """Mirrors VALIDATE-INPUT-KEY-FIELDS in COTRN02C."""

    def test_neither_card_nor_acct_raises(self):
        payload = {**VALID_PAYLOAD}
        del payload["card_num"]
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**payload)
        assert "Account or Card Number must be entered" in str(exc_info.value)

    def test_acct_id_non_numeric_raises(self):
        payload = {**VALID_PAYLOAD, "acct_id": "ABC123", "card_num": None}
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**payload)
        assert "Account ID must be Numeric" in str(exc_info.value)

    def test_card_num_non_numeric_raises(self):
        payload = {**VALID_PAYLOAD, "card_num": "ABCD111111111111"}
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**payload)
        assert "Card Number must be Numeric" in str(exc_info.value)

    def test_valid_card_num_accepted(self):
        req = TransactionValidateRequest(**VALID_PAYLOAD)
        assert req.card_num == "4111111111111111"

    def test_valid_acct_id_accepted(self):
        payload = {**VALID_PAYLOAD, "acct_id": "00000000001", "card_num": None}
        req = TransactionValidateRequest(**payload)
        assert req.acct_id == "00000000001"


class TestDataFieldValidation:
    """Mirrors VALIDATE-INPUT-DATA-FIELDS in COTRN02C."""

    def test_empty_tran_type_cd_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_type_cd": ""})
        assert "Type CD can NOT be empty" in str(exc_info.value)

    def test_non_numeric_tran_type_cd_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_type_cd": "AB"})
        assert "Type CD must be Numeric" in str(exc_info.value)

    def test_empty_tran_cat_cd_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_cat_cd": ""})
        assert "Category CD can NOT be empty" in str(exc_info.value)

    def test_non_numeric_tran_cat_cd_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_cat_cd": "ABCD"})
        assert "Category CD must be Numeric" in str(exc_info.value)

    def test_empty_source_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_source": ""})
        assert "Source can NOT be empty" in str(exc_info.value)

    def test_empty_desc_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_desc": ""})
        assert "Description can NOT be empty" in str(exc_info.value)

    # Amount format tests (pos1=sign, pos2-9=digits, pos10='.', pos11-12=digits)
    def test_empty_amount_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_amt": ""})
        assert "Amount can NOT be empty" in str(exc_info.value)

    def test_amount_without_sign_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_amt": "00000052.47"})
        assert "Amount should be in format -99999999.99" in str(exc_info.value)

    def test_amount_too_short_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_amt": "-52.47"})
        assert "Amount should be in format -99999999.99" in str(exc_info.value)

    def test_amount_positive_sign_accepted(self):
        req = TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_amt": "+00000250.00"})
        assert req.tran_amt == "+00000250.00"

    def test_amount_negative_sign_accepted(self):
        req = TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_amt": "-00000052.47"})
        assert req.tran_amt == "-00000052.47"

    # Date format tests (YYYY-MM-DD)
    def test_empty_orig_date_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_orig_dt": ""})
        assert "Orig Date can NOT be empty" in str(exc_info.value)

    def test_orig_date_wrong_format_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_orig_dt": "01/15/2026"})
        assert "Orig Date should be in format YYYY-MM-DD" in str(exc_info.value)

    def test_orig_date_invalid_calendar_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_orig_dt": "2026-02-30"})
        assert "Not a valid date" in str(exc_info.value)

    def test_empty_proc_date_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_proc_dt": ""})
        assert "Proc Date can NOT be empty" in str(exc_info.value)

    def test_proc_date_wrong_format_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_proc_dt": "20260315"})
        assert "Proc Date should be in format YYYY-MM-DD" in str(exc_info.value)

    def test_merchant_id_non_numeric_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_merchant_id": "ABCDE1234"})
        assert "Merchant ID must be Numeric" in str(exc_info.value)

    def test_empty_merchant_name_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_merchant_name": ""})
        assert "Merchant Name can NOT be empty" in str(exc_info.value)

    def test_empty_merchant_city_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_merchant_city": ""})
        assert "Merchant City can NOT be empty" in str(exc_info.value)

    def test_empty_merchant_zip_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionValidateRequest(**{**VALID_PAYLOAD, "tran_merchant_zip": ""})
        assert "Merchant Zip can NOT be empty" in str(exc_info.value)


class TestConfirmationValidation:
    """Mirrors PROCESS-ENTER-KEY EVALUATE CONFIRMI in COTRN02C."""

    def test_confirm_y_accepted(self):
        req = TransactionCreate(**{**VALID_PAYLOAD, "confirm": "Y"})
        assert req.confirm == "Y"

    def test_confirm_lowercase_y_accepted(self):
        req = TransactionCreate(**{**VALID_PAYLOAD, "confirm": "y"})
        assert req.confirm == "Y"

    def test_confirm_n_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**{**VALID_PAYLOAD, "confirm": "N"})
        assert "Confirm to add this transaction" in str(exc_info.value)

    def test_confirm_other_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**{**VALID_PAYLOAD, "confirm": "X"})
        assert "Invalid value. Valid values are (Y/N)" in str(exc_info.value)
