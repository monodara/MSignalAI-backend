import aiosqlite
import os
from app.config.settings import SQLITE_DB_FILE

if os.environ.get("K_SERVICE"):  
    DB_PATH = "/tmp/database.db"
else:
    DB_PATH = SQLITE_DB_FILE

async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        yield db

async def create_stock_price_table():
    async with aiosqlite.connect(SQLITE_DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stock_prices (
                symbol TEXT NOT NULL,
                datetime TEXT NOT NULL,
                interval TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY(symbol, datetime, interval)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS income_statements (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                reportedCurrency TEXT,
                cik TEXT,
                fillingDate TEXT,
                acceptedDate TEXT,
                calendarYear TEXT,
                period TEXT,
                revenue REAL,
                costOfRevenue REAL,
                grossProfit REAL,
                grossProfitRatio REAL,
                researchAndDevelopmentExpenses REAL,
                generalAndAdministrativeExpenses REAL,
                sellingAndMarketingExpenses REAL,
                otherExpenses REAL,
                operatingExpenses REAL,
                operatingIncome REAL,
                operatingIncomeRatio REAL,
                interestIncome REAL,
                interestExpense REAL,
                totalOtherIncomeExpensesNet REAL,
                incomeBeforeTax REAL,
                incomeBeforeTaxRatio REAL,
                incomeTaxExpense REAL,
                netIncome REAL,
                netIncomeRatio REAL,
                eps REAL,
                epsdiluted REAL,
                weightedAverageShsOut REAL,
                weightedAverageShsOutDil REAL,
                link TEXT,
                finalLink TEXT,
                PRIMARY KEY(symbol, date)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS balance_sheets (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                reportedCurrency TEXT,
                cik TEXT,
                fillingDate TEXT,
                acceptedDate TEXT,
                calendarYear TEXT,
                period TEXT,
                cashAndCashEquivalents REAL,
                shortTermInvestments REAL,
                cashAndShortTermInvestments REAL,
                netReceivables REAL,
                inventory REAL,
                otherCurrentAssets REAL,
                totalCurrentAssets REAL,
                propertyPlantEquipmentNet REAL,
                goodwill REAL,
                intangibleAssets REAL,
                goodwillAndIntangibleAssets REAL,
                longTermInvestments REAL,
                taxAssets REAL,
                otherNonCurrentAssets REAL,
                totalNonCurrentAssets REAL,
                totalAssets REAL,
                accountPayables REAL,
                shortTermDebt REAL,
                taxPayables REAL,
                deferredRevenue REAL,
                otherCurrentLiabilities REAL,
                totalCurrentLiabilities REAL,
                longTermDebt REAL,
                deferredRevenueNonCurrent REAL,
                deferredTaxLiabilitiesNonCurrent REAL,
                otherNonCurrentLiabilities REAL,
                totalNonCurrentLiabilities REAL,
                totalLiabilities REAL,
                commonStock REAL,
                retainedEarnings REAL,
                accumulatedOtherComprehensiveIncomeLoss REAL,
                otherTotalEquity REAL,
                totalEquity REAL,
                totalLiabilitiesAndEquity REAL,
                totalInvestments REAL,
                totalDebt REAL,
                netDebt REAL,
                link TEXT,
                finalLink TEXT,
                PRIMARY KEY(symbol, date)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cash_flow_statements (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                reportedCurrency TEXT,
                cik TEXT,
                fillingDate TEXT,
                acceptedDate TEXT,
                calendarYear TEXT,
                period TEXT,
                netIncome REAL,
                depreciationAndAmortization REAL,
                deferredIncomeTax REAL,
                stockBasedCompensation REAL,
                changeInWorkingCapital REAL,
                accountsReceivables REAL,
                inventory REAL,
                accountsPayables REAL,
                otherWorkingCapital REAL,
                otherNonCashItems REAL,
                netCashProvidedByOperatingActivities REAL,
                investmentsInPropertyPlantAndEquipment REAL,
                purchasesOfInvestments REAL,
                salesMaturitiesOfInvestments REAL,
                otherInvestingActivites REAL,
                netCashUsedForInvestingActivites REAL,
                debtRepayment REAL,
                commonStockIssued REAL,
                commonStockRepurchased REAL,
                dividendsPaid REAL,
                otherFinancingActivites REAL,
                netCashUsedForFinancingActivities REAL,
                effectOfForexChangesOnCash REAL,
                netChangeInCash REAL,
                cashAtEndOfPeriod REAL,
                cashAtBeginningOfPeriod REAL,
                operatingCashFlow REAL,
                capitalExpenditure REAL,
                freeCashFlow REAL,
                link TEXT,
                finalLink TEXT,
                PRIMARY KEY(symbol, date)
            )
        """)
        await db.commit()

async def close_db_connection():
    # No explicit close needed for aiosqlite with 'async with'
    pass
