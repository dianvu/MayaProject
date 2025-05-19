import os, sys
import streamlit as st
import json
import calendar
from datetime import datetime
from utils.report_generator import ReportGenerator
from utils.config import anthropic_llm
from utils.data_fetcher import DataFetcher

# Set page config
st.set_page_config(
    page_title="Financial Report Generator",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if 'report_data' not in st.session_state:
    st.session_state.report_data = None

def main():
    st.title("Financial Report Generator")
    st.write("Generate personalized financial reports using different prompting techniques.")

    # Sidebar for input parameters
    st.sidebar.header("Report Parameters")
    
    # User ID input
    user_id = st.sidebar.text_input("User ID", "")
    
    # Date selection
    current_year = datetime.now().year
    current_month = datetime.now().month
    year = st.sidebar.selectbox(
        "Year",
        [current_year-1, current_year],
        index=1
    )
    
    month = st.sidebar.selectbox(
        "Month",
        range(1, 13),
        index=current_month-1
    )
    
    # Initialize components
    llm = anthropic_llm()
    data_fetcher = DataFetcher("data/transactions.csv", "data/transactions.db")
    
    # Generate report button
    if st.sidebar.button("Generate Report"):
        with st.spinner("Generating report..."):
            try:
                # Fetch transaction data
                transaction_summary = data_fetcher.monthly_profile(year, month, user_id)
                
                # Initialize report generator
                report_generator = ReportGenerator(llm, user_id, year, month)
                
                # Generate report
                report_data = report_generator.generate_report(transaction_summary)
                
                # Save report
                report_generator.save_report(report_data)
                
                # Store in session state
                st.session_state.report_data = report_data
                
                st.success("Report generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
    
    # Display report if available
    if st.session_state.report_data:
        report = st.session_state.report_data
        
        # Display metadata
        st.header("Report Metadata")
        
        # User ID on its own row
        st.metric("User ID", report["metadata"]["user_id"])
        
        # Year and Month on the next row
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Year", report["metadata"]["year"])
        with col2:
            st.metric("Month", report["metadata"]["month"])
        
        # Display chosen prompting approaches
        st.header("Best Prompting Approaches")
        for component, approach in report.get("best_approaches", {}).items():
            st.write(f"**{component.replace('_', ' ').title()}**: {approach}")
        
        # Executive Summary
        st.write(report["report_components"]["executive_summary"])
        
        # Recommendations
        st.write(report["report_components"]["recommendations"])
        
        # Evaluation Metrics
        st.header("Evaluation Metrics")
        
        # Create two columns for metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Executive Summary")
            metrics = report["evaluations"]["executive_summary"]
            st.metric("Ethical Flag", metrics["ethical_flag"])
            st.metric("Confidence", f"{metrics['confidence']:.2f}")
            st.metric("Similarity Score", f"{metrics['similarity_score']:.2f}")
        
        with col2:
            st.subheader("Recommendations")
            metrics = report["evaluations"]["recommendations"]
            st.metric("Ethical Flag", metrics["ethical_flag"])
            st.metric("Confidence", f"{metrics['confidence']:.2f}")
            st.metric("Similarity Score", f"{metrics['similarity_score']:.2f}")
        
        # Download button for JSON
        json_str = json.dumps(report, indent=4)
        st.download_button(
            label="Download Report as JSON",
            data=json_str,
            file_name=f"report_{user_id}_{year}_{calendar.month_name[month]}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()