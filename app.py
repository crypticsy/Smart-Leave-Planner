import streamlit as st
import pandas as pd

from datetime import datetime
from utils import LeaveOptimizer, create_calendar_html

# Page configuration
st.set_page_config(
    page_title="Smart Leave Planner",
    page_icon="📅",
    layout="wide"
)

divider_color = "red"

# Custom CSS for better calendar styling
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    # Year selection
    current_year = datetime.now().year
    year = st.sidebar.selectbox(
        "Select Year",
        options=[current_year, current_year + 1],
        index=0
    )
    st.sidebar.markdown("<br/>", unsafe_allow_html=True)
    
    
    # Country selection
    country = st.sidebar.selectbox(
        "Select Country",
        options=['GB', 'US', 'CA', 'AU', 'DE', 'FR', 'IN', 'JP'],
        index=0,
        help="This determines which public holidays to consider"
    )
    st.sidebar.markdown("<br/>", unsafe_allow_html=True)
    
    
    # Number of leave days
    num_leaves = st.sidebar.number_input(
        "Annual Leave Days Available",
        min_value=1,
        max_value=50,
        value=20,
        help="Enter the number of annual leave days you have"
    )
    
    st.sidebar.markdown("<br/>", unsafe_allow_html=True)
    
    # Preferred months filter
    all_months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    
    preferred_months = st.sidebar.multiselect(
        "Select preferred months for taking leave",
        options=all_months,
        help="Choose specific months when you prefer to take leave. Leave empty to consider all months."
    )
    
    if not preferred_months:
      preferred_months = all_months  # Default to all months if none selected
    
    # Convert month names to numbers
    month_name_to_num = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    
    preferred_month_nums = [month_name_to_num[month] for month in preferred_months] if preferred_months else list(range(1, 13))
    
    # Create optimizer
    optimizer = LeaveOptimizer(year, country)
    
    # Calculate optimal leave days
    with st.spinner("Calculating optimal leave strategy..."):
        optimal_leaves, total_days_off, leaves_used = optimizer.get_optimal_leave_days(num_leaves, preferred_month_nums)
    
    # Display results
    col1, col2, col3, col4 = st.columns(4)
    st.markdown("<br/>", unsafe_allow_html=True)
    
    with col1:
        st.metric("Total Days Off", total_days_off)
    
    with col2:
        st.metric("Leave Days Used", f"{leaves_used}/{num_leaves}")
    
    with col3:
        efficiency = total_days_off / leaves_used if leaves_used > 0 else 0
        st.metric("Efficiency Ratio", f"{efficiency:.1f}:1")
    
    with col4:
        st.metric("Preferred Months", len(preferred_months))
    
    # Show strategy breakdown
    st.subheader("📊 &nbsp; Strategy Breakdown", divider=divider_color)
    
    # Count weekends and holidays
    total_weekends = len([d for d in optimizer.weekends if d.year == year])
    total_holidays = len(optimizer.holidays)
    
    breakdown_data = {
        "Category": ["Weekends", "Public Holidays", "Optimal Leave Days", "Total Days Off"],
        "Days": [total_weekends, total_holidays, leaves_used, total_days_off]
    }
    
    breakdown_df = pd.DataFrame(breakdown_data)
    st.dataframe(breakdown_df, use_container_width=True)
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Show optimal leave dates
    if optimal_leaves:
        st.subheader("🎯 &nbsp; Recommended Leave Dates", divider=divider_color)

        # Group leave dates by month
        leave_by_month = {}
        for leave_date in optimal_leaves:
            month_year = leave_date.strftime("%B %Y")
            if month_year not in leave_by_month:
                leave_by_month[month_year] = []
            leave_by_month[month_year].append(leave_date.strftime("%A, %B %d"))

        # Sort months by date
        sorted_months = sorted(leave_by_month.keys(), key=lambda x: datetime.strptime(x, "%B %Y"))

        # Display months in rows of 4 columns with spacing
        for i in range(0, len(sorted_months), 4):
            cols = st.columns(4)
            for j, month in enumerate(sorted_months[i:i+4]):
                with cols[j]:
                    st.markdown(f"**{month}**")
                    for date in leave_by_month[month]:
                        st.markdown(f"- {date}")
            st.markdown("<br>", unsafe_allow_html=True)  # Adds visual gap between rows
    else:
        st.subheader("🎯 &nbsp; Recommended Leave Dates", divider=divider_color)
        if not preferred_months:
            st.warning("Please select at least one preferred month to see recommendations.")
        else:
            st.info("No optimal leave opportunities found in your preferred months. Try selecting additional months or reducing your leave day constraints.")
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Display calendar
    st.subheader("📅  &nbsp; Annual Calendar View", divider=divider_color)
    calendar_html = create_calendar_html(year, optimizer.holidays, optimal_leaves)
    st.markdown(calendar_html, unsafe_allow_html=True)
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Additional insights
    st.subheader("💡  &nbsp; Insights", divider=divider_color)
    
    insights = []
    
    if efficiency > 3:
        insights.append("🎉 &nbsp; Excellent efficiency! You're getting great value from your leave days.")
    elif efficiency > 2:
        insights.append("👍 &nbsp; Good efficiency! Your leave strategy is well-optimized.")
    else:
        insights.append("💭 &nbsp; Consider timing your leave around holidays and weekends for better efficiency.")
    
    if leaves_used < num_leaves:
        remaining = num_leaves - leaves_used
        insights.append(f"📝 &nbsp; You have {remaining} leave days remaining. Consider using them for personal time or vacation.")
        
        if len(preferred_months) < 12:
            insights.append(f"🗓️ &nbsp; You've selected {len(preferred_months)} preferred months. Consider expanding your options for better optimization.")
    
    if not preferred_months:
        insights.append("⚠️ &nbsp; Please select at least one preferred month to get personalized recommendations.")
    
    for insight in insights:
        st.info(insight)
    st.markdown("<br/>", unsafe_allow_html=True)
        
    # Show public holidays
    st.subheader("🏛️ &nbsp; Public Holidays", divider=divider_color)
    holidays_df = pd.DataFrame([
        {"Date": date.strftime("%A, %B %d, %Y"), "Holiday": name}
        for date, name in optimizer.holidays.items()
    ])
    st.dataframe(holidays_df, use_container_width=True)
    
    

if __name__ == "__main__":
    main()