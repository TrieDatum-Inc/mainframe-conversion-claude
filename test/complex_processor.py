def process_transaction(transaction, user, config):
    result = {"status": "unknown", "errors": [], "warnings": []}

    if transaction is None:
        result["status"] = "error"
        result["errors"].append("Transaction is null")
        return result

    if user is None:
        result["status"] = "error"
        result["errors"].append("User is null")
        return result

    if transaction.get("type") == "credit":
        if transaction.get("amount") > 10000:
            if user.get("verified"):
                if user.get("tier") == "gold":
                    result["status"] = "approved"
                    if transaction.get("currency") == "USD":
                        result["fee"] = transaction["amount"] * 0.01
                    elif transaction.get("currency") == "EUR":
                        result["fee"] = transaction["amount"] * 0.015
                    else:
                        result["fee"] = transaction["amount"] * 0.02
                        if config.get("strict_mode"):
                            result["warnings"].append("Non-standard currency in strict mode")
                            if transaction.get("country") not in config.get("allowed_countries", []):
                                result["status"] = "pending_review"
                                result["errors"].append("Country not in allowed list")
                elif user.get("tier") == "silver":
                    if transaction.get("amount") > 50000:
                        result["status"] = "pending_review"
                        if config.get("auto_escalate"):
                            result["status"] = "escalated"
                            if user.get("history", {}).get("flags", 0) > 3:
                                result["status"] = "blocked"
                                result["errors"].append("Too many flags for high-value silver transaction")
                            else:
                                if transaction.get("recurring"):
                                    result["status"] = "approved"
                                    result["warnings"].append("Auto-approved recurring transaction")
                    else:
                        result["status"] = "approved"
                        result["fee"] = transaction["amount"] * 0.025
                else:
                    result["status"] = "denied"
                    result["errors"].append("Unverified tier for high-value credit")
                    if config.get("allow_override"):
                        if user.get("manager_approved"):
                            result["status"] = "approved"
                            result["warnings"].append("Manager override applied")
                        else:
                            if user.get("pending_approval"):
                                result["status"] = "pending_review"
                            else:
                                result["errors"].append("No override available")
            else:
                result["status"] = "denied"
                result["errors"].append("User not verified for high-value transaction")
        else:
            result["status"] = "approved"
            if user.get("new_account"):
                if transaction.get("amount") > 1000:
                    result["warnings"].append("New account moderate transaction")
                    if config.get("new_account_limit"):
                        if transaction["amount"] > config["new_account_limit"]:
                            result["status"] = "pending_review"
    elif transaction.get("type") == "debit":
        if transaction.get("amount") > user.get("balance", 0):
            result["status"] = "denied"
            result["errors"].append("Insufficient balance")
            if config.get("allow_overdraft"):
                if user.get("overdraft_enabled"):
                    overdraft_limit = user.get("overdraft_limit", 500)
                    if transaction["amount"] - user["balance"] <= overdraft_limit:
                        result["status"] = "approved"
                        result["warnings"].append("Overdraft used")
                    else:
                        result["errors"].append("Exceeds overdraft limit")
                        if user.get("tier") == "gold":
                            result["status"] = "pending_review"
                            result["warnings"].append("Gold tier overdraft escalation")
        else:
            result["status"] = "approved"
            if transaction.get("amount") > 5000:
                if not user.get("two_factor_verified"):
                    result["status"] = "pending_review"
                    result["errors"].append("2FA required for large debit")
    elif transaction.get("type") == "transfer":
        if transaction.get("destination"):
            if transaction["destination"].get("internal"):
                result["status"] = "approved"
                if transaction["amount"] > 25000:
                    result["warnings"].append("Large internal transfer")
            else:
                if user.get("verified") and user.get("tier") in ("gold", "silver"):
                    result["status"] = "approved"
                    if transaction.get("country") != user.get("country"):
                        result["warnings"].append("Cross-border transfer")
                        if transaction["amount"] > 10000:
                            result["status"] = "pending_review"
                            if config.get("compliance_check"):
                                result["errors"].append("Compliance review required")
                else:
                    result["status"] = "denied"
                    result["errors"].append("External transfers require verified silver/gold tier")
        else:
            result["status"] = "error"
            result["errors"].append("No destination specified")
    else:
        result["status"] = "error"
        result["errors"].append("Unknown transaction type")
        if config.get("log_unknown"):
            result["warnings"].append("Unknown type logged for review")

    return result
