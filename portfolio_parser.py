import pandas as pd


def process_portfolio(portfolio_path):
    # Load client portfolio (assumed in Excel format)
    df = pd.read_excel(portfolio_path)

    # Clean or process the data as needed, extract necessary columns
    # For example, extract columns like CUSIP, Shares, etc.
    df["Trade Date Quantity"] = df["Trade Date Quantity"].fillna(0).astype(int)
    df["Market Value"] = df["Market Value"].fillna(0).astype(int)

    portfolio_data = []
    for index, row in df.iterrows():
        portfolio_data.append(
            {
                "CUSIP": row["CUSIP"],
                "Shares": row["Trade Date Quantity"],
                "Market Value": row["Market Value"],
                # Add more fields as needed
            }
        )

    return portfolio_data
