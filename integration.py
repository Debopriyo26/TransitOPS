import sqlite3
from datetime import datetime

def check_driver_validity(driver_row):
    """Enforce security validation procedures assessing operational suitability constraints[cite: 3].
    
    Returns tuple: (bool, description_string)
    """
    
    if driver_row['status'] == 'Suspended':
        return False, "Driver Operative carries an active system suspension status flag[cite: 3]."
    
    if driver_row['status'] == 'Off Duty':
        return False, "Operator is currently registered as Off Duty[cite: 3]."
        
    
    try:
        expiry = datetime.strptime(driver_row['expiry_date'], '%Y-%m-%d')
        if expiry.date() < datetime.now().date():
            return False, "Driver qualification validation rejected: Driving license parameters have expired[cite: 3]."
    except ValueError:
        return False, "Malformed context date configuration logs found in profile index."
        
    return True, "Operational authorization verified."

def check_vehicle_dispatch_availability(vehicle_row):
    """Scan machine parameters against exclusion matrices prior to routing actions[cite: 3]."""
    forbidden_states = ['In Shop', 'Retired']
    if vehicle_row['status'] in forbidden_states:
        return False, f"Asset is unavailable for routing workflows due to: '{vehicle_row['status']}' state tracking[cite: 3]."
    return True, "Asset tracking parameter matches deployment availability metrics."

from database.database import get_db_connection
from datetime import datetime

def run_dispatch_validation(db_path, vehicle_ref, driver_ref, cargo_weight):
    """Enforce complete cross-checks prior to commitment routines[cite: 3].
    
    Returns tuple: (bool, error_message_string)
    """
    conn = get_db_connection(db_path)
    
    vehicle = conn.execute('SELECT * FROM vehicles WHERE reg_num = ?', (vehicle_ref,)).fetchone()
    driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (driver_ref,)).fetchone()
    
    conn.close()
    
    if not vehicle:
        return False, "Target deployment vehicle identifier could not be verified."
    if not driver:
        return False, "Assigned operator identity reference is missing from directories."
        
    
    if cargo_weight > vehicle['max_capacity']:
        return False, f"Cargo weight ({cargo_weight} KG) breaks max payload bounds ({vehicle['max_capacity']} KG)[cite: 3]."
        
    
    if vehicle['status'] != 'Available':
        return False, f"Selected asset is disqualified due to active status flag: '{vehicle['status']}'[cite: 3]."
        
    if driver['status'] != 'Available':
        return False, f"Assigned driver operator is non-eligible due to current status: '{driver['status']}'[cite: 3]."
        
    
    if driver['status'] == 'Suspended':
        return False, "Operative is flagged as Suspended across company records[cite: 3]."
        
    try:
        expiry_date = datetime.strptime(driver['expiry_date'], '%Y-%m-%d').date()
        if expiry_date < datetime.now().date():
            return False, f"Operator licensing expiration threshold breached on date: {driver['expiry_date']}[cite: 3]."
    except ValueError:
        return False, "Internal validation engine failed to parse operator date signature format."

    return True, "All validation checkpoints passed successfully."
def calculate_vehicle_operational_costs(db_path):
    """Compute total operational costs (Fuel + Maintenance + Expenses) per vehicle."""
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT reg_num, model FROM vehicles").fetchall()
    
    summaries = []
    for v in vehicles:
        reg = v['reg_num']
        
        # Sum Fuel Costs
        fuel_row = conn.execute("SELECT SUM(cost) as total FROM fuel_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
        fuel_cost = round(fuel_row['total'] or 0.0, 2)
        
        # Sum Maintenance Costs
        maint_row = conn.execute("SELECT SUM(cost) as total FROM maintenance_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
        maint_cost = round(maint_row['total'] or 0.0, 2)
        
        # Sum General Expenses
        gen_row = conn.execute("SELECT SUM(cost) as total FROM expenses WHERE vehicle_ref = ?", (reg,)).fetchone()
        gen_cost = round(gen_row['total'] or 0.0, 2)
        
        total_cost = round(fuel_cost + maint_cost + gen_cost, 2)
        
        summaries.append({
            'reg_num': reg,
            'model': v['model'],
            'fuel_cost': fuel_cost,
            'maint_cost': maint_cost,
            'gen_cost': gen_cost,
            'total_cost': total_cost
        })
        
    conn.close()
    return summaries
def get_dashboard_kpis(db_path):
    """Calculate real-time KPIs for the main dashboard layout."""
    conn = get_db_connection(db_path)
    
    total_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles").fetchone()['c']
    avail_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles WHERE status='Available'").fetchone()['c']
    active_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles WHERE status='On Trip'").fetchone()['c']
    maint_veh = conn.execute("SELECT COUNT(*) as c FROM vehicles WHERE status='In Shop'").fetchone()['c']
    
    active_trips = conn.execute("SELECT COUNT(*) as c FROM trips WHERE status='Dispatched'").fetchone()['c']
    drivers_duty = conn.execute("SELECT COUNT(*) as c FROM drivers WHERE status='On Trip'").fetchone()['c']
    
    # Fleet Utilization = (Active Vehicles / Total Vehicles) * 100
    utilization = round((active_veh / total_veh * 100) if total_veh > 0 else 0.0, 1)
    
    conn.close()
    return {
        'active_vehicles': active_veh,
        'available_vehicles': avail_veh,
        'maintenance_vehicles': maint_veh,
        'active_trips': active_trips,
        'drivers_duty': drivers_duty,
        'utilization': utilization
    }

def get_analytics_data(db_path):
    """Compute Fuel Efficiency and Vehicle ROI formulas per vehicle."""
    conn = get_db_connection(db_path)
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    
    analytics = []
    for v in vehicles:
        reg = v['reg_num']
        acq_cost = v['acquisition_cost']
        
        # Fuel consumed
        fuel_row = conn.execute("SELECT SUM(liters) as l, SUM(cost) as c FROM fuel_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
        fuel_liters = fuel_row['l'] or 0.0
        fuel_cost = fuel_row['c'] or 0.0
        
        # Distance traveled (Total planned distance of trips)
        dist_row = conn.execute("SELECT SUM(planned_distance) as d FROM trips WHERE vehicle_ref = ?", (reg,)).fetchone()
        distance = dist_row['d'] or 0.0
        
        # Maintenance Costs
        maint_row = conn.execute("SELECT SUM(cost) as c FROM maintenance_logs WHERE vehicle_ref = ?", (reg,)).fetchone()
        maint_cost = maint_row['c'] or 0.0
        
        # Formula: Fuel Efficiency = Distance / Fuel Consumed
        efficiency = round(distance / fuel_liters, 2) if fuel_liters > 0 else 0.0
        
        # Mocking Revenue for ROI: Assume standard freight rate of 50 INR per KM traveled
        revenue = distance * 50.0
        
        # Formula: ROI = (Revenue - (Maint + Fuel)) / Acq Cost
        roi = round(((revenue - (maint_cost + fuel_cost)) / acq_cost) * 100, 2) if acq_cost > 0 else 0.0
        
        analytics.append({
            'reg_num': reg,
            'efficiency': efficiency,
            'operational_cost': fuel_cost + maint_cost,
            'roi': roi
        })
        
    conn.close()
    return analytics