
import calendar
import holidays
from datetime import datetime, timedelta


class LeaveOptimizer:
    def __init__(self, year, country='GB'):
        self.year = year
        self.country = country
        self.holidays = holidays.country_holidays(country, years=year)
        self.weekends = self.get_weekends()
        
    def get_weekends(self):
        """Get all weekend dates for the year"""
        weekends = []
        start_date = datetime(self.year, 1, 1)
        end_date = datetime(self.year, 12, 31)
        
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in [5, 6]:  # Saturday = 5, Sunday = 6
                weekends.append(current_date.date())
            current_date += timedelta(days=1)
        
        return weekends
    
    def get_optimal_leave_days(self, num_leaves, preferred_months=None):
        """Find optimal leave days to maximize total days off"""
        if preferred_months is None:
            preferred_months = list(range(1, 13))  # All months
            
        # Get all possible leave strategies
        strategies = []
        
        # Strategy 1: Bridge holidays with weekends
        bridge_opportunities = self.find_bridge_opportunities(preferred_months)
        
        # Strategy 2: Create long weekends
        long_weekend_opportunities = self.find_long_weekend_opportunities(preferred_months)
        
        # Combine and rank strategies
        all_opportunities = bridge_opportunities + long_weekend_opportunities
        
        # Sort by efficiency (days off per leave day)
        all_opportunities.sort(key=lambda x: x['efficiency'], reverse=True)
        
        # Select best combination within leave budget
        selected_leaves = []
        total_leaves_used = 0
        total_days_off = 0
        used_date_ranges = []
        
        for opportunity in all_opportunities:
            # Check if this opportunity overlaps with already selected dates
            if not self.has_date_overlap(opportunity['leave_dates'], used_date_ranges):
                if total_leaves_used + opportunity['leaves_needed'] <= num_leaves:
                    selected_leaves.extend(opportunity['leave_dates'])
                    total_leaves_used += opportunity['leaves_needed']
                    total_days_off += opportunity['total_days_off']
                    
                    # Add this date range to used ranges
                    used_date_ranges.append(opportunity['leave_dates'])
        
        return selected_leaves, total_days_off, total_leaves_used
    
    def has_date_overlap(self, new_dates, existing_ranges):
        """Check if new dates overlap with existing date ranges"""
        for date in new_dates:
            for existing_range in existing_ranges:
                if date in existing_range:
                    return True
        return False
    
    def find_bridge_opportunities(self, preferred_months):
        """Find opportunities to bridge holidays with weekends"""
        opportunities = []
        
        for holiday_date in self.holidays:
            if isinstance(holiday_date, datetime):
                holiday_date = holiday_date.date()
            
            # Skip if holiday is not in preferred months
            if holiday_date.month not in preferred_months:
                continue
            
            # Check if we can bridge before the holiday
            before_opportunity = self.analyze_bridge_before(holiday_date)
            if before_opportunity:
                opportunities.append(before_opportunity)
            
            # Check if we can bridge after the holiday
            after_opportunity = self.analyze_bridge_after(holiday_date)
            if after_opportunity:
                opportunities.append(after_opportunity)
        
        return opportunities
    
    def analyze_bridge_before(self, holiday_date):
        """Analyze bridging opportunity before a holiday"""
        # Look for weekend before holiday
        days_before = []
        current_date = holiday_date - timedelta(days=1)
        
        while current_date.weekday() not in [5, 6] and len(days_before) < 4:
            days_before.append(current_date)
            current_date -= timedelta(days=1)
        
        if current_date.weekday() in [5, 6] and days_before:
            # Found a weekend before, calculate efficiency
            weekend_days = []
            check_date = current_date
            while check_date.weekday() in [5, 6]:
                weekend_days.append(check_date)
                check_date -= timedelta(days=1)
            
            total_days_off = len(days_before) + len(weekend_days) + 1  # +1 for holiday
            leaves_needed = len(days_before)
            
            if leaves_needed > 0:
                return {
                    'leave_dates': days_before,
                    'total_days_off': total_days_off,
                    'leaves_needed': leaves_needed,
                    'efficiency': total_days_off / leaves_needed,
                    'description': f"Bridge before {self.holidays[holiday_date]}"
                }
        
        return None
    
    def analyze_bridge_after(self, holiday_date):
        """Analyze bridging opportunity after a holiday"""
        # Look for weekend after holiday
        days_after = []
        current_date = holiday_date + timedelta(days=1)
        
        while current_date.weekday() not in [5, 6] and len(days_after) < 4:
            days_after.append(current_date)
            current_date += timedelta(days=1)
        
        if current_date.weekday() in [5, 6] and days_after:
            # Found a weekend after, calculate efficiency
            weekend_days = []
            check_date = current_date
            while check_date.weekday() in [5, 6]:
                weekend_days.append(check_date)
                check_date += timedelta(days=1)
            
            total_days_off = len(days_after) + len(weekend_days) + 1  # +1 for holiday
            leaves_needed = len(days_after)
            
            if leaves_needed > 0:
                return {
                    'leave_dates': days_after,
                    'total_days_off': total_days_off,
                    'leaves_needed': leaves_needed,
                    'efficiency': total_days_off / leaves_needed,
                    'description': f"Bridge after {self.holidays[holiday_date]}"
                }
        
        return None
    
    def find_long_weekend_opportunities(self, preferred_months):
        """Find opportunities to create long weekends"""
        opportunities = []
        
        # Find Fridays and Mondays that can create 4-day weekends
        start_date = datetime(self.year, 1, 1)
        end_date = datetime(self.year, 12, 31)
        
        current_date = start_date
        while current_date <= end_date:
            # Skip if not in preferred months
            if current_date.month not in preferred_months:
                current_date += timedelta(days=1)
                continue
                
            if current_date.weekday() == 4:  # Friday
                # Check if Monday is not a holiday and in preferred months
                monday = current_date + timedelta(days=3)
                if (monday.date() not in self.holidays and 
                    monday <= end_date and 
                    monday.month in preferred_months):
                    opportunities.append({
                        'leave_dates': [monday.date()],
                        'total_days_off': 4,
                        'leaves_needed': 1,
                        'efficiency': 4.0,
                        'description': f"Long weekend (Fri-Mon) starting {current_date.strftime('%b %d')}"
                    })
            
            elif current_date.weekday() == 0:  # Monday
                # Check if Friday is not a holiday and in preferred months
                friday = current_date - timedelta(days=3)
                if (friday.date() not in self.holidays and 
                    friday >= start_date and 
                    friday.month in preferred_months):
                    opportunities.append({
                        'leave_dates': [friday.date()],
                        'total_days_off': 4,
                        'leaves_needed': 1,
                        'efficiency': 4.0,
                        'description': f"Long weekend (Fri-Mon) ending {current_date.strftime('%b %d')}"
                    })
            
            current_date += timedelta(days=1)
        
        return opportunities

def create_calendar_html(year, holidays_dict, optimal_leaves):
    """Create HTML calendar for the year with 3 months per row"""
    html = f"""
    <div class="calendar-container">
        <h2 style="text-align: center; color: #2c3e50;">Annual Leave Calendar for {year}</h2>
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: #e74c3c;"></div>
                <span>Public Holidays</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #3498db;"></div>
                <span>Optimal Leave Days</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #2ecc71;"></div>
                <span>Extended Weekends</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #ecf0f1;"></div>
                <span>Weekends</span>
            </div>
        </div>
    """
    
    # Create calendar in quarters (2 months per row)
    quarters = [
        [1, 2],    # Q1: Jan, Feb
        [3, 4],    # Q2: Mar, Apr
        [5, 6],    # Q3: May, Jun
        [7, 8],    # Q4: Jul, Aug
        [9, 10],   # Q5: Sep, Oct
        [11, 12]   # Q6: Nov, Dec
    ] 
    
    for quarter in quarters:
        html += '<div style="display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap;">'
        
        for month in quarter:
            month_name = calendar.month_name[month]
            html += f'''
            <div style="flex: 1; min-width: 300px;">
                <div class="month-header">{month_name} {year}</div>
                <div class="calendar-grid">
            '''
            
            # Day headers
            for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                html += f'<div class="day-header">{day}</div>'
            
            # Get calendar for month
            cal = calendar.monthcalendar(year, month)
            
            for week in cal:
                for day in week:
                    if day == 0:
                        html += '<div class="day-cell"></div>'
                    else:
                        date_obj = datetime(year, month, day).date()
                        day_class = "day-cell"
                        
                        # Check day type
                        if date_obj.weekday() in [5, 6]:  # Weekend
                            day_class += " weekend"
                        
                        if date_obj in holidays_dict:  # Holiday
                            day_class += " holiday"
                            title = holidays_dict[date_obj]
                        elif date_obj in optimal_leaves:  # Optimal leave day
                            day_class += " optimal-leave"
                            title = "Optimal Leave Day"
                        else:
                            title = ""
                        
                        html += f'<div class="{day_class}" title="{title}">{day}</div>'
            
            html += '</div></div>'  # Close calendar-grid and month container
        
        html += '</div>'  # Close quarter row
    
    html += '</div>'  # Close calendar-container
    return html