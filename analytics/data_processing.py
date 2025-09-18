import os
import csv
import statistics
from datetime import datetime, timedelta
from collections import defaultdict
from config import Config

def load_analytics_data():
    """Your existing function"""
    data = []
    with open(Config.ANALYTICS_FILE, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'hour' in row and 'consumption' in row and row['hour'] is not None and row['consumption'] is not None:
                try:
                    data.append({
                        'date': row['date'],
                        'hour': int(row['hour']),
                        'consumption': float(row['consumption'])
                    })
                except (ValueError, TypeError):
                    continue
    return data

def process_hourly_data(data):
    """Process data for last 24 hours view"""
    now = datetime.now()
    last_24h = now - timedelta(hours=24)
    
    hourly_data = defaultdict(float)
    
    for record in data:
        record_datetime = datetime.strptime(f"{record['date']} {record['hour']:02d}:00:00", "%Y-%m-%d %H:%M:%S")
        if record_datetime >= last_24h:
            hour_label = record_datetime.strftime("%H:00")
            hourly_data[hour_label] = record['consumption']
    
    # Fill missing hours with 0
    labels = []
    values = []
    for i in range(24):
        hour_label = f"{i:02d}:00"
        labels.append(hour_label)
        values.append(hourly_data.get(hour_label, 0))
    
    return {'labels': labels, 'values': values}

def process_weekly_data(data):
    """Process data for last 7 days view"""
    now = datetime.now()
    last_7_days = now - timedelta(days=7)
    
    daily_data = defaultdict(float)
    daily_counts = defaultdict(int)
    
    for record in data:
        record_date = datetime.strptime(record['date'], "%Y-%m-%d")
        if record_date >= last_7_days:
            day_label = record_date.strftime("%Y-%m-%d")
            daily_data[day_label] += record['consumption']
            daily_counts[day_label] += 1
    
    # Average consumption per day
    for day in daily_data:
        if daily_counts[day] > 0:
            daily_data[day] = daily_data[day] / daily_counts[day]
    
    labels = []
    values = []
    for i in range(7):
        date = (now - timedelta(days=6-i)).strftime("%Y-%m-%d")
        day_name = (now - timedelta(days=6-i)).strftime("%a")
        labels.append(day_name)
        values.append(daily_data.get(date, 0))
    
    return {'labels': labels, 'values': values}

def process_yearly_data(data):
    """Process data for last 12 months view"""
    now = datetime.now()
    monthly_data = defaultdict(float)
    monthly_counts = defaultdict(int)
    
    for record in data:
        record_date = datetime.strptime(record['date'], "%Y-%m-%d")
        if (now - record_date).days <= 365:
            month_label = record_date.strftime("%Y-%m")
            monthly_data[month_label] += record['consumption']
            monthly_counts[month_label] += 1
    
    # Average consumption per month
    for month in monthly_data:
        if monthly_counts[month] > 0:
            monthly_data[month] = monthly_data[month] / monthly_counts[month]
    
    labels = []
    values = []
    for i in range(12):
        date = now.replace(day=1) - timedelta(days=30*i)
        month_label = date.strftime("%Y-%m")
        month_name = date.strftime("%b %Y")
        labels.insert(0, month_name)
        values.insert(0, monthly_data.get(month_label, 0))
    
    return {'labels': labels, 'values': values}

def calculate_statistics(data):
    """Calculate comprehensive statistics"""
    now = datetime.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    this_month_data = []
    last_month_data = []
    all_consumption = []
    peak_usage = 0
    peak_time = ""
    
    for record in data:
        record_date = datetime.strptime(record['date'], "%Y-%m-%d")
        consumption = record['consumption']
        all_consumption.append(consumption)
        
        # Track peak usage
        if consumption > peak_usage:
            peak_usage = consumption
            peak_time = f"{record['date']} {record['hour']:02d}:00"
        
        # Monthly comparison
        if record_date >= this_month_start:
            this_month_data.append(consumption)
        elif record_date >= last_month_start and record_date < this_month_start:
            last_month_data.append(consumption)
    
    # Calculate statistics
    total_consumption = sum(this_month_data) if this_month_data else 0
    average_daily = total_consumption / max(1, len(set(record['date'] for record in data 
                    if datetime.strptime(record['date'], "%Y-%m-%d") >= this_month_start)))
    
    # Calculate monthly change
    this_month_avg = statistics.mean(this_month_data) if this_month_data else 0
    last_month_avg = statistics.mean(last_month_data) if last_month_data else 0
    daily_change = ((this_month_avg - last_month_avg) / max(last_month_avg, 1)) * 100 if last_month_avg > 0 else 0
    
    estimated_cost = total_consumption * Config.ELECTRICITY_RATE
    
    return {
        'total_consumption': total_consumption,
        'average_daily': average_daily,
        'peak_usage': peak_usage,
        'peak_time': peak_time,
        'daily_change': daily_change,
        'estimated_cost': estimated_cost
    }

def analyze_peak_usage(data):
    """Analyze peak usage by hour of day"""
    hourly_peaks = defaultdict(list)
    
    for record in data:
        hour = record['hour']
        consumption = record['consumption']
        hourly_peaks[hour].append(consumption)
    
    labels = [f"{i:02d}:00" for i in range(24)]
    values = []
    
    for i in range(24):
        if i in hourly_peaks and hourly_peaks[i]:
            values.append(max(hourly_peaks[i]))
        else:
            values.append(0)
    
    return {'labels': labels, 'values': values}

def calculate_usage_distribution(data):
    """Calculate usage distribution for pie chart"""
    all_consumption = [record['consumption'] for record in data]
    if not all_consumption:
        return [25, 25, 25, 25]  # Default equal distribution
    
    # Define usage categories based on percentiles
    sorted_consumption = sorted(all_consumption)
    total_records = len(sorted_consumption)
    
    q1 = sorted_consumption[total_records // 4]
    q2 = sorted_consumption[total_records // 2]
    q3 = sorted_consumption[3 * total_records // 4]
    
    low_count = sum(1 for c in all_consumption if c <= q1)
    medium_count = sum(1 for c in all_consumption if q1 < c <= q2)
    high_count = sum(1 for c in all_consumption if q2 < c <= q3)
    peak_count = sum(1 for c in all_consumption if c > q3)
    
    return [low_count, medium_count, high_count, peak_count]

def calculate_weekly_pattern(data):
    """Calculate average usage by day of week"""
    daily_totals = defaultdict(list)
    
    for record in data:
        record_date = datetime.strptime(record['date'], "%Y-%m-%d")
        day_of_week = record_date.weekday()  # 0 = Monday
        daily_totals[day_of_week].append(record['consumption'])
    
    # Calculate averages for each day
    weekly_averages = []
    for i in range(7):  # Monday to Sunday
        if i in daily_totals and daily_totals[i]:
            avg = statistics.mean(daily_totals[i])
            weekly_averages.append(round(avg, 2))
        else:
            weekly_averages.append(0)
    
    return weekly_averages

def calculate_cost_breakdown(total_consumption):
    """Calculate detailed cost breakdown"""
    base_charges = 150.0  # Fixed monthly charge
    energy_charges = total_consumption * Config.ELECTRICITY_RATE
    tax_surcharge = (base_charges + energy_charges) * 0.15  # 15% tax
    
    total = base_charges + energy_charges + tax_surcharge
    
    return {
        'base_charges': base_charges,
        'energy_charges': energy_charges,
        'tax_surcharge': tax_surcharge,
        'total': total
    }

def generate_efficiency_insights(data, stats):
    """Generate efficiency insights and recommendations"""
    insights = []
    
    # Calculate efficiency score
    all_consumption = [record['consumption'] for record in data]
    avg_consumption = statistics.mean(all_consumption) if all_consumption else 0
    optimal_consumption = 60  # Assumed optimal consumption
    efficiency_score = max(0, min(100, 100 - (avg_consumption - optimal_consumption) / optimal_consumption * 100))
    
    # Generate insights based on data
    if stats['peak_usage'] > 100:
        insights.append({
            'type': 'warning',
            'message': f'High peak usage detected ({stats["peak_usage"]:.1f} kWh). Consider load balancing during peak hours.'
        })
    
    if stats['daily_change'] > 10:
        insights.append({
            'type': 'warning',
            'message': f'Usage increased by {stats["daily_change"]:.1f}% this month. Review your energy habits.'
        })
    elif stats['daily_change'] < -10:
        insights.append({
            'type': 'success',
            'message': f'Great! Usage decreased by {abs(stats["daily_change"]):.1f}% this month.'
        })
    
    if avg_consumption < optimal_consumption:
        insights.append({
            'type': 'success',
            'message': 'Your consumption is below the optimal range. Excellent energy management!'
        })
    
    # Time-based insights
    peak_hour = int(stats['peak_time'].split(' ')[1].split(':')[0]) if stats['peak_time'] else 12
    if 9 <= peak_hour <= 17:
        insights.append({
            'type': 'info',
            'message': 'Peak usage occurs during business hours. Consider time-of-use optimization.'
        })
    
    return {
        'score': round(efficiency_score),
        'insights': insights
    }

# Additional utility functions for advanced features
def calculate_carbon_footprint(consumption_kwh):
    """Calculate carbon footprint based on consumption"""
    # Average carbon emission factor for electricity in India: ~0.82 kg CO2/kWh
    carbon_factor = 0.82
    return consumption_kwh * carbon_factor

def predict_next_month_usage(data):
    """Simple prediction for next month's usage based on trends"""
    if len(data) < 30:  # Need at least 30 data points
        return None
    
    recent_data = data[-720:]  # Last 30 days (assuming hourly data)
    recent_avg = statistics.mean([record['consumption'] for record in recent_data])
    
    # Simple trend calculation
    older_data = data[-1440:-720] if len(data) >= 1440 else data[:-720]
    if older_data:
        older_avg = statistics.mean([record['consumption'] for record in older_data])
        trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        predicted_usage = recent_avg * (1 + trend) * 30 * 24  # Monthly prediction
        return max(0, predicted_usage)
    
    return recent_avg * 30 * 24  # Simple monthly projection
