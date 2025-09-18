import csv
import json
import tempfile
from datetime import datetime
from flask import Blueprint, jsonify, send_file
from flask_login import login_required
from analytics.data_processing import (
    load_analytics_data, calculate_statistics, calculate_cost_breakdown,
    calculate_carbon_footprint, predict_next_month_usage
)
from config import Config

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/get-analytics', methods=['GET'])
@login_required
def get_analytics():
    try:
        analytics_data = load_analytics_data()
        
        # Aggregate data by hour, day, and month
        hourly_data = {str(i): 0 for i in range(24)}
        daily_data = {}
        monthly_data = {}
        for record in analytics_data:
            # Hourly aggregation
            hour = record['hour']
            hourly_data[str(hour)] += record['consumption']
            
            # Daily aggregation
            date = record['date']
            daily_data[date] = daily_data.get(date, 0) + record['consumption']
            # Monthly aggregation
            month = date[:7] # YYYY-MM
            monthly_data[month] = monthly_data.get(month, 0) + record['consumption']
        
        # Calculate stats
        total_consumption = sum(d['consumption'] for d in analytics_data)
        highest_usage = max(d['consumption'] for d in analytics_data) if analytics_data else 0
        average_usage = total_consumption / len(analytics_data) if analytics_data else 0
        # Placeholder for savings calculation
        estimated_savings = total_consumption * 0.15 # 15% arbitrary saving
        
        stats = {
            "highest_usage": highest_usage,
            "average_usage": average_usage,
            "savings": estimated_savings,
            # Additional stats for advanced dashboard
            "total_consumption": total_consumption,
            "average_daily": total_consumption / max(1, len(set(record['date'] for record in analytics_data))),
            "peak_usage": highest_usage,
            "peak_time": "12:00 PM",  # Placeholder
            "daily_change": 5.2,  # Placeholder percentage change
            "estimated_cost": total_consumption * Config.ELECTRICITY_RATE
        }
        
        # Convert your existing data format to match frontend expectations
        # Transform hourly data for last 24 hours
        hourly_labels = [f"{i:02d}:00" for i in range(24)]
        hourly_values = [hourly_data.get(str(i), 0) for i in range(24)]
        
        # Transform daily data for last 7 days (get most recent 7 days)
        sorted_daily = sorted(daily_data.items(), key=lambda x: x[0], reverse=True)[:7]
        weekly_labels = [datetime.strptime(date, "%Y-%m-%d").strftime("%a") for date, _ in reversed(sorted_daily)]
        weekly_values = [value for _, value in reversed(sorted_daily)]
        
        # Transform monthly data for last 12 months
        sorted_monthly = sorted(monthly_data.items(), key=lambda x: x[0], reverse=True)[:12]
        yearly_labels = [datetime.strptime(f"{month}-01", "%Y-%m-%d").strftime("%b %Y") for month, _ in reversed(sorted_monthly)]
        yearly_values = [value for _, value in reversed(sorted_monthly)]
        
        # Generate additional analytics for advanced features
        peak_analysis = {
            'labels': hourly_labels,
            'values': [max(80, hourly_data.get(str(i), 0) + (i * 2)) for i in range(24)]  # Mock peak data
        }
        
        distribution = [25, 35, 25, 15]  # Mock distribution data
        
        weekly_pattern = [65, 70, 68, 72, 75, 85, 80]  # Mock weekly pattern
        
        cost_breakdown = calculate_cost_breakdown(total_consumption)
        
        efficiency_insights = [
            {"type": "success", "message": "Your consumption is optimized during off-peak hours."},
            {"type": "warning", "message": "Consider reducing usage during peak hours (6-9 PM)."},
            {"type": "info", "message": "Switch to LED bulbs for 20% energy savings."}
        ]
        
        return jsonify({
            "stats": stats,
            "hourly": {"labels": hourly_labels, "values": hourly_values},
            "weekly": {"labels": weekly_labels, "values": weekly_values},
            "yearly": {"labels": yearly_labels, "values": yearly_values},
            "peak_analysis": peak_analysis,
            "distribution": distribution,
            "weekly_pattern": weekly_pattern,
            "cost_breakdown": cost_breakdown,
            "efficiency_insights": efficiency_insights,
            "efficiency_score": 78
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@analytics_bp.route('/export-data')
@login_required
def export_data():
    """Export analytics data in various formats"""
    from flask import request
    format_type = request.args.get('format', 'csv').lower()
    
    try:
        raw_data = load_analytics_data()
        if not raw_data:
            return jsonify({'error': 'No data to export'}), 404
        
        if format_type == 'csv':
            # Create temporary CSV file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            
            fieldnames = ['date', 'hour', 'consumption', 'cost']
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in raw_data:
                writer.writerow({
                    'date': record['date'],
                    'hour': f"{record['hour']:02d}:00",
                    'consumption': record['consumption'],
                    'cost': round(record['consumption'] * Config.ELECTRICITY_RATE, 2)
                })
            
            temp_file.close()
            
            return send_file(
                temp_file.name,
                as_attachment=True,
                download_name=f'energy_consumption_{datetime.now().strftime("%Y%m%d")}.csv',
                mimetype='text/csv'
            )
        
        elif format_type == 'json':
            # Export as JSON
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_records': len(raw_data),
                'data': raw_data,
                'summary': calculate_statistics(raw_data)
            }
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(export_data, temp_file, indent=2)
            temp_file.close()
            
            return send_file(
                temp_file.name,
                as_attachment=True,
                download_name=f'energy_analytics_{datetime.now().strftime("%Y%m%d")}.json',
                mimetype='application/json'
            )
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@analytics_bp.route('/efficiency-tips')
@login_required
def get_efficiency_tips():
    """Get personalized efficiency tips based on usage patterns"""
    try:
        raw_data = load_analytics_data()
        if not raw_data:
            return jsonify({'error': 'No data available'}), 404
        
        stats = calculate_statistics(raw_data)
        tips = []
        
        # Generate tips based on usage patterns
        if stats['peak_usage'] > 80:
            tips.append({
                'category': 'Peak Usage',
                'tip': 'Your peak usage is high. Consider using high-power appliances during off-peak hours.',
                'potential_savings': '15-20%'
            })
        
        if stats['daily_change'] > 5:
            tips.append({
                'category': 'Usage Trend',
                'tip': 'Your consumption has increased recently. Check for inefficient appliances or changed habits.',
                'potential_savings': '10-15%'
            })
        
        # Time-based tips
        from collections import defaultdict
        import statistics
        hourly_usage = defaultdict(list)
        for record in raw_data:
            hourly_usage[record['hour']].append(record['consumption'])
        
        peak_hours = []
        for hour, consumptions in hourly_usage.items():
            if consumptions and statistics.mean(consumptions) > 70:
                peak_hours.append(hour)
        
        if any(9 <= hour <= 17 for hour in peak_hours):
            tips.append({
                'category': 'Time Management',
                'tip': 'High usage during business hours detected. Shift non-essential loads to night time.',
                'potential_savings': '8-12%'
            })
        
        # Seasonal tips
        current_month = datetime.now().month
        if current_month in [6, 7, 8]:  # Summer months
            tips.append({
                'category': 'Seasonal',
                'tip': 'Summer peak detected. Optimize AC usage and consider better insulation.',
                'potential_savings': '20-25%'
            })
        
        return jsonify({
            'tips': tips,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate tips: {str(e)}'}), 500

@analytics_bp.route('/predictions')
@login_required
def get_predictions():
    """Get usage predictions and projections"""
    try:
        raw_data = load_analytics_data()
        if not raw_data:
            return jsonify({'error': 'Insufficient data for predictions'}), 404
        
        next_month_prediction = predict_next_month_usage(raw_data)
        current_month_consumption = sum(record['consumption'] for record in raw_data 
                                      if datetime.strptime(record['date'], "%Y-%m-%d").month == datetime.now().month)
        
        predictions = {
            'next_month_kwh': round(next_month_prediction, 2) if next_month_prediction else None,
            'next_month_cost': round(next_month_prediction * Config.ELECTRICITY_RATE, 2) if next_month_prediction else None,
            'carbon_footprint': round(calculate_carbon_footprint(current_month_consumption), 2),
            'projected_annual': round(current_month_consumption * 12, 2) if current_month_consumption else 0
        }
        
        return jsonify(predictions)
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate predictions: {str(e)}'}), 500
