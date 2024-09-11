import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import pandas as pd
from lxml import etree
import json


def generate_xml(sec_data, portfolio_data, output_file):
    ns = {
        "ns1": "http://www.sec.gov/edgar/document/thirteenf/informationtable",
    }

    # Create the root element with the correct namespace prefix
    root = etree.Element(
        "{http://www.sec.gov/edgar/document/thirteenf/informationtable}informationTable",
        nsmap=ns,
    )

    portfolio_data = [
        portfolio_item
        for portfolio_item in portfolio_data
        if portfolio_item["Market Value"] > 200000 and portfolio_item["Shares"] > 10000
    ]

    for portfolio_item in portfolio_data:
        # Find the corresponding item from SEC data
        matching_sec_data = next(
            (item for item in sec_data if item["cusip_no"] == portfolio_item["CUSIP"]),
            None,
        )

        if matching_sec_data:
            info_table = etree.SubElement(
                root,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}infoTable",
            )
            # Add elements to infoTable
            etree.SubElement(
                info_table,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}nameOfIssuer",
            ).text = matching_sec_data["issuer_name"]
            etree.SubElement(
                info_table,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}titleOfClass",
            ).text = matching_sec_data.get("issuer_description", "")
            etree.SubElement(
                info_table,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}cusip",
            ).text = matching_sec_data["cusip_no"]
            if pd.notna(portfolio_item.get("FIGI")):
                etree.SubElement(
                    info_table,
                    "{http://www.sec.gov/edgar/document/thirteenf/informationtable}figi",
                ).text = matching_sec_data.get("FIGI", "")
            etree.SubElement(
                info_table,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}value",
            ).text = str(portfolio_item["Market Value"])
            shrs_or_prn_amt = etree.SubElement(
                info_table,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}shrsOrPrnAmt",
            )
            etree.SubElement(
                shrs_or_prn_amt,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}sshPrnamt",
            ).text = str(portfolio_item["Shares"])
            etree.SubElement(
                shrs_or_prn_amt,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}sshPrnamtType",
            ).text = "SH"
            if pd.notna(portfolio_item.get("PutOrCall")):
                etree.SubElement(
                    info_table,
                    "{http://www.sec.gov/edgar/document/thirteenf/informationtable}putCall",
                ).text = ""

            etree.SubElement(
                info_table,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}investmentDiscretion",
            ).text = "SOLE"

            voting_auth = etree.SubElement(
                info_table,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}votingAuthority",
            )
            etree.SubElement(
                voting_auth,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}Sole",
            ).text = "0"
            etree.SubElement(
                voting_auth,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}Shared",
            ).text = "0"
            etree.SubElement(
                voting_auth,
                "{http://www.sec.gov/edgar/document/thirteenf/informationtable}None",
            ).text = str(portfolio_item["Shares"])

    # Write the XML data to file with pretty print
    tree = etree.ElementTree(root)
    xml_str = etree.tostring(root, encoding="utf-8", method="xml")
    parsed = minidom.parseString(xml_str)
    pretty_xml_str = parsed.toprettyxml(indent="  ")
    # Convert sec_data and portfolio_data to pandas DataFrames
    sec_df = pd.DataFrame(sec_data)
    portfolio_df = pd.DataFrame(portfolio_data)

    # Rename 'cusip_no' column in sec_df to match 'CUSIP' in portfolio_df
    sec_df.rename(columns={"cusip_no": "CUSIP"}, inplace=True)

    # Merge the two DataFrames on the 'CUSIP' field (inner join)
    combined_df = pd.merge(portfolio_df, sec_df, on="CUSIP", how="inner")

    # Create the required format by selecting and renaming columns
    combined_df = combined_df.assign(
        NameOfIssuer=combined_df["issuer_name"],
        TitleOfClass=combined_df["issuer_description"],
        FIGI="",  # FIGI is empty
        Value=combined_df["Market Value"],
        Shares=combined_df["Shares"],
        SharesOrPrincipal="SH",  # Assuming SH for shares, this can be modified
        PutOrCall=combined_df.apply(
            lambda row: (
                row["issuer_description"]
                if row["issuer_description"] in ["CALL", "PUT"]
                else ""
            ),
            axis=1,
        ),
        InvestmentDiscretion="SOLE",  # Empty field
        OtherManagers="",  # Empty field
        Sole=0,  # Assuming 0 for Sole
        Shared=0,  # Assuming 0 for Shared
        NoneValue=combined_df["Shares"],  # 'None' equals to 'Shares'
    )

    # Select the final columns
    final_columns = [
        "NameOfIssuer",
        "TitleOfClass",
        "CUSIP",
        "FIGI",
        "Value",
        "Shares",
        "SharesOrPrincipal",
        "PutOrCall",
        "InvestmentDiscretion",
        "OtherManagers",
        "Sole",
        "Shared",
        "NoneValue",
    ]

    # Select only the necessary columns
    final_df = combined_df[final_columns]

    # Rename 'NoneValue' to 'None' (since None is a keyword in Python)
    final_df.rename(columns={"NoneValue": "None"}, inplace=True)

    # Display the combined DataFrame
  
    # Optionally save the result to an Excel file
    final_df.to_excel("combined_data.xlsx", index=False)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty_xml_str)
