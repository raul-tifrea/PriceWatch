"""Script to run the Streamlit dashboard."""
import sys
from streamlit.web import cli as stcli

def main():
    sys.argv = ["streamlit", "run", "pricewatch/presentation/dashboard.py"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
