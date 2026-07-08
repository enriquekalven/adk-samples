import os
import sys
import argparse
import json
from dotenv import load_dotenv

# Load credentials from active agent .env file if it exists
load_dotenv("/Users/enriq/Documents/adk-samples/python/agents/economic-research-agent/.env")

# Import the local skill scripts from the same directory
from trade_skill import fetch_regional_trade_data
from workforce_exposure_skill import analyze_workforce_exposure
from labor_shift_skill import model_labor_shifts
from mls_property_analysis_skill import fetch_mls_property_listings

def main():
    parser = argparse.ArgumentParser(
        description="Economic Analysis Suite - Standalone CLI Runner\n"
                    "Allows running economic research calculations without deploying an agent.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available analysis commands")
    
    # 1. Trade
    parser_trade = subparsers.add_parser("trade", help="Fetch regional trade flow data")
    parser_trade.add_argument("--states", nargs="+", required=True, help="List of states (e.g. Texas 'North Carolina')")
    parser_trade.add_argument("--commodity", default="Electronic Products", help="Commodity type")
    
    # 2. Exposure
    parser_exp = subparsers.add_parser("exposure", help="Analyze occupational AI exposure")
    parser_exp.add_argument("--jobs", nargs="+", required=True, help="Job titles (e.g. 'Software Developers' 'Financial Analysts')")
    
    # 3. Disruption
    parser_shift = subparsers.add_parser("disruption", help="Forecast MSA labor disruption indices")
    parser_shift.add_argument("--cities", nargs="+", required=True, help="Target MSA cities (e.g. Austin Columbus)")
    
    # 4. Property MLS
    parser_mls = subparsers.add_parser("properties", help="Find property listings and Cap Rates")
    parser_mls.add_argument("--city", required=True, help="Target city (e.g. Columbus)")
    parser_mls.add_argument("--type", default="multifamily", help="Property type: multifamily, single-family, condo")
    
    args = parser.parse_args()
    
    if args.command == "trade":
        res = fetch_regional_trade_data(args.states, args.commodity)
        print(res)
    elif args.command == "exposure":
        res = classify_exposure_with_fallback(args.jobs)
        print(res)
    elif args.command == "disruption":
        res = model_labor_shifts(args.cities)
        print(res)
    elif args.command == "properties":
        res = fetch_mls_property_listings(args.city, property_type=args.type)
        print(res)

def classify_exposure_with_fallback(jobs):
    # Set default GCP configuration if running locally and unset
    if not os.getenv("GCP_PROJECT") and not os.getenv("GOOGLE_CLOUD_PROJECT"):
        os.environ["GCP_PROJECT"] = "project-maui"
    if not os.getenv("GCP_LOCATION"):
        os.environ["GCP_LOCATION"] = "us-central1"
    return analyze_workforce_exposure(jobs)

if __name__ == "__main__":
    main()
