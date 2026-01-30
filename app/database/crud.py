from typing import List, Dict, Any

import aiosqlite
from app.config.settings import SQLITE_DB_FILE

async def insert_stock_data(
    symbol: str,
    interval: str,
    data: list[dict],
):
    async with aiosqlite.connect(SQLITE_DB_FILE) as db:
        await db.executemany(
            """
            INSERT OR IGNORE INTO stock_prices (
                symbol,
                datetime,
                interval,
                open,
                high,
                low,
                close,
                volume
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    symbol,
                    entry["datetime"],
                    interval,
                    float(entry["open"]),
                    float(entry["high"]),
                    float(entry["low"]),
                    float(entry["close"]),
                    int(entry["volume"]) if entry.get("volume") else None,
                )
                for entry in data
            ],
        )
        await db.commit()


async def get_historical_data_from_db(symbol: str, interval: str):
    async with aiosqlite.connect(SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row # Return rows as dict-like objects
        cursor = await db.execute(
            "SELECT datetime, open, high, low, close, volume FROM stock_prices WHERE symbol = ? AND interval = ? ORDER BY datetime ASC",
            (symbol, interval)
        )
        history = await cursor.fetchall()
        return [dict(row) for row in history]

async def insert_income_statement(symbol: str, statement: Dict[str, Any]) -> None:
    async with aiosqlite.connect(SQLITE_DB_FILE) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO income_statements (
                symbol, date, reportedCurrency, cik, fillingDate, acceptedDate,
                calendarYear, period, revenue, costOfRevenue, grossProfit,
                grossProfitRatio, researchAndDevelopmentExpenses,
                generalAndAdministrativeExpenses, sellingAndMarketingExpenses,
                otherExpenses, operatingExpenses, operatingIncome,
                operatingIncomeRatio, interestIncome, interestExpense,
                totalOtherIncomeExpensesNet, incomeBeforeTax,
                incomeBeforeTaxRatio, incomeTaxExpense, netIncome,
                netIncomeRatio, eps, epsdiluted, weightedAverageShsOut,
                weightedAverageShsOutDil, link, finalLink
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol, statement.get("date"), statement.get("reportedCurrency"),
                statement.get("cik"), statement.get("fillingDate"), statement.get("acceptedDate"),
                statement.get("calendarYear"), statement.get("period"), statement.get("revenue"),
                statement.get("costOfRevenue"), statement.get("grossProfit"),
                statement.get("grossProfitRatio"), statement.get("researchAndDevelopmentExpenses"),
                statement.get("generalAndAdministrativeExpenses"), statement.get("sellingAndMarketingExpenses"),
                statement.get("otherExpenses"), statement.get("operatingExpenses"), statement.get("operatingIncome"),
                statement.get("operatingIncomeRatio"), statement.get("interestIncome"), statement.get("interestExpense"),
                statement.get("totalOtherIncomeExpensesNet"), statement.get("incomeBeforeTax"),
                statement.get("incomeBeforeTaxRatio"), statement.get("incomeTaxExpense"), statement.get("netIncome"),
                statement.get("netIncomeRatio"), statement.get("eps"), statement.get("epsdiluted"),
                statement.get("weightedAverageShsOut"), statement.get("weightedAverageShsOutDil"),
                statement.get("link"), statement.get("finalLink")
            )
        )
        await db.commit()
    return None

async def get_income_statements_from_db(symbol: str, limit: int = 4, period: str = "quarter") -> List[Dict[str, Any]]:
    async with aiosqlite.connect(SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM income_statements
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (symbol, limit)
        )
        statements = await cursor.fetchall()
        return [dict(row) for row in statements]

async def insert_balance_sheet(symbol: str, statement: Dict[str, Any]) -> None:
    async with aiosqlite.connect(SQLITE_DB_FILE) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO balance_sheets (
                symbol, date, reportedCurrency, cik, fillingDate, acceptedDate,
                calendarYear, period, cashAndCashEquivalents, shortTermInvestments,
                cashAndShortTermInvestments, netReceivables, inventory,
                otherCurrentAssets, totalCurrentAssets, propertyPlantEquipmentNet,
                goodwill, intangibleAssets, goodwillAndIntangibleAssets,
                longTermInvestments, taxAssets, otherNonCurrentAssets,
                totalNonCurrentAssets, totalAssets, accountPayables,
                shortTermDebt, taxPayables, deferredRevenue,
                otherCurrentLiabilities, totalCurrentLiabilities, longTermDebt,
                deferredRevenueNonCurrent, deferredTaxLiabilitiesNonCurrent,
                otherNonCurrentLiabilities, totalNonCurrentLiabilities,
                totalLiabilities, commonStock, retainedEarnings,
                accumulatedOtherComprehensiveIncomeLoss, otherTotalEquity,
                totalEquity, totalLiabilitiesAndEquity, totalInvestments,
                totalDebt, netDebt, link, finalLink
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol, statement.get("date"), statement.get("reportedCurrency"),
                statement.get("cik"), statement.get("fillingDate"), statement.get("acceptedDate"),
                statement.get("calendarYear"), statement.get("period"), statement.get("cashAndCashEquivalents"),
                statement.get("shortTermInvestments"), statement.get("cashAndShortTermInvestments"),
                statement.get("netReceivables"), statement.get("inventory"),
                statement.get("otherCurrentAssets"), statement.get("totalCurrentAssets"),
                statement.get("propertyPlantEquipmentNet"), statement.get("goodwill"),
                statement.get("intangibleAssets"), statement.get("goodwillAndIntangibleAssets"),
                statement.get("longTermInvestments"), statement.get("taxAssets"),
                statement.get("otherNonCurrentAssets"), statement.get("totalNonCurrentAssets"),
                statement.get("totalAssets"), statement.get("accountPayables"),
                statement.get("shortTermDebt"), statement.get("taxPayables"),
                statement.get("deferredRevenue"), statement.get("otherCurrentLiabilities"),
                statement.get("totalCurrentLiabilities"), statement.get("longTermDebt"),
                statement.get("deferredRevenueNonCurrent"), statement.get("deferredTaxLiabilitiesNonCurrent"),
                statement.get("otherNonCurrentLiabilities"), statement.get("totalNonCurrentLiabilities"),
                statement.get("totalLiabilities"), statement.get("commonStock"),
                statement.get("retainedEarnings"), statement.get("accumulatedOtherComprehensiveIncomeLoss"),
                statement.get("otherTotalEquity"), statement.get("totalEquity"),
                statement.get("totalLiabilitiesAndEquity"), statement.get("totalInvestments"),
                statement.get("totalDebt"), statement.get("netDebt"), statement.get("link"),
                statement.get("finalLink")
            )
        )
        await db.commit()
    return None

async def get_balance_sheets_from_db(symbol: str, limit: int = 4, period: str = "quarter") -> List[Dict[str, Any]]:
    async with aiosqlite.connect(SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM balance_sheets
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (symbol, limit)
        )
        statements = await cursor.fetchall()
        return [dict(row) for row in statements]

async def insert_cash_flow_statement(symbol: str, statement: Dict[str, Any]) -> None:
    async with aiosqlite.connect(SQLITE_DB_FILE) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO cash_flow_statements (
                symbol, date, reportedCurrency, cik, fillingDate, acceptedDate,
                calendarYear, period, netIncome, depreciationAndAmortization,
                deferredIncomeTax, stockBasedCompensation, changeInWorkingCapital,
                accountsReceivables, inventory, accountsPayables,
                otherWorkingCapital, otherNonCashItems,
                netCashProvidedByOperatingActivities,
                investmentsInPropertyPlantAndEquipment, purchasesOfInvestments,
                salesMaturitiesOfInvestments, otherInvestingActivites,
                netCashUsedForInvestingActivites, debtRepayment,
                commonStockIssued, commonStockRepurchased, dividendsPaid,
                otherFinancingActivites, netCashUsedForFinancingActivities,
                effectOfForexChangesOnCash, netChangeInCash, cashAtEndOfPeriod,
                cashAtBeginningOfPeriod, operatingCashFlow,
                capitalExpenditure, freeCashFlow, link, finalLink
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol, statement.get("date"), statement.get("reportedCurrency"),
                statement.get("cik"), statement.get("fillingDate"), statement.get("acceptedDate"),
                statement.get("calendarYear"), statement.get("period"), statement.get("netIncome"),
                statement.get("depreciationAndAmortization"), statement.get("deferredIncomeTax"),
                statement.get("stockBasedCompensation"), statement.get("changeInWorkingCapital"),
                statement.get("accountsReceivables"), statement.get("inventory"),
                statement.get("accountsPayables"), statement.get("otherWorkingCapital"),
                statement.get("otherNonCashItems"), statement.get("netCashProvidedByOperatingActivities"),
                statement.get("investmentsInPropertyPlantAndEquipment"), statement.get("purchasesOfInvestments"),
                statement.get("salesMaturitiesOfInvestments"), statement.get("otherInvestingActivites"),
                statement.get("netCashUsedForInvestingActivites"), statement.get("debtRepayment"),
                statement.get("commonStockIssued"), statement.get("commonStockRepurchased"),
                statement.get("dividendsPaid"), statement.get("otherFinancingActivites"),
                statement.get("netCashUsedForFinancingActivities"), statement.get("effectOfForexChangesOnCash"),
                statement.get("netChangeInCash"), statement.get("cashAtEndOfPeriod"),
                statement.get("cashAtBeginningOfPeriod"), statement.get("operatingCashFlow"),
                statement.get("capitalExpenditure"), statement.get("freeCashFlow"), statement.get("link"),
                statement.get("finalLink")
            )
        )
        await db.commit()
    return None

async def get_cash_flow_statements_from_db(symbol: str, limit: int = 4, period: str = "quarter") -> List[Dict[str, Any]]:
    async with aiosqlite.connect(SQLITE_DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM cash_flow_statements
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (symbol, limit)
        )
        statements = await cursor.fetchall()
        return [dict(row) for row in statements]
