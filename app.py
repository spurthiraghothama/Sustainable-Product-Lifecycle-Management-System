from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "secret123"

GRADE_SCORE = {'A': 4, 'B': 3, 'C': 2, 'D': 1}

# -------------------------
# 1) DASHBOARD / HOME
# -------------------------
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS cnt FROM Products")
    total_products = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) AS cnt FROM Components")
    total_components = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) AS cnt FROM RawMaterials")
    total_materials = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) AS cnt FROM Suppliers")
    total_suppliers = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) AS cnt FROM ProductInstances")
    total_instances = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) AS cnt FROM LifecycleEvents")
    total_events = cursor.fetchone()['cnt']

    cursor.execute("""
        SELECT EventType, COUNT(*) AS cnt
        FROM LifecycleEvents
        GROUP BY EventType
    """)
    rows = cursor.fetchall()
    dist = {r['EventType']: r['cnt'] for r in rows}
    recycled = dist.get('Recycled', 0) + dist.get('Recycled_Hazardous', 0)
    disposed = dist.get('Disposed', 0)
    repair = dist.get('Repair', 0)

    cursor.execute("""
        SELECT cc.WeightInGrams, rm.RecyclableGrade
        FROM ComponentComposition cc
        JOIN RawMaterials rm ON cc.MaterialID = rm.MaterialID
    """)
    comp_rows = cursor.fetchall()
    total_weight = sum(float(r['WeightInGrams']) for r in comp_rows)
    weighted_score_sum = sum(float(r['WeightInGrams']) * GRADE_SCORE.get(r['RecyclableGrade'], 0) for r in comp_rows)
    overall_recyclability_score = round(weighted_score_sum / total_weight, 2) if total_weight > 0 else 0

    conn.close()
    return render_template(
        'index.html',
        total_products=total_products,
        total_components=total_components,
        total_materials=total_materials,
        total_suppliers=total_suppliers,
        total_instances=total_instances,
        total_events=total_events,
        recycled=recycled,
        disposed=disposed,
        repair=repair,
        overall_recyclability_score=overall_recyclability_score
    )


# -------------------------
# 2) PRODUCT INSTANCE REGISTRATION
# -------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT ProductID, ModelName FROM Products")
    products = cursor.fetchall()

    cursor.execute("""
        SELECT pi.InstanceID, pi.SerialNumber,
               COALESCE((SELECT le.EventType FROM LifecycleEvents le
                         WHERE le.InstanceID = pi.InstanceID
                         ORDER BY le.EventDate DESC LIMIT 1), 'NoEvents') AS current_state,
               pi.ProductID
        FROM ProductInstances pi
        ORDER BY pi.InstanceID DESC LIMIT 10
    """)
    recent = cursor.fetchall()

    if request.method == 'POST':
        serial = request.form['serial'].strip()
        product_id = request.form['product_id']
        try:
            cursor.callproc('RegisterProductInstance', [serial, product_id])
            conn.commit()
            flash('✅ Product instance registered successfully!', 'success')
        except Exception as e:
            flash(f'⚠️ {e}', 'error')
        return redirect(url_for('register'))

    conn.close()
    return render_template('register.html', products=products, recent=recent)


# -------------------------
# 3) LIFECYCLE EVENTS PAGE
# -------------------------
@app.route('/instance_detail', methods=['GET', 'POST'])
def instance_detail():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT InstanceID, SerialNumber FROM ProductInstances")
    instances = cursor.fetchall()

    timeline = []
    selected = None

    if request.method == 'POST':
        inst_id = int(request.form['instance_id'])
        event_type = request.form['event_type']
        try:
            cursor.callproc('AddLifecycleEvent', [inst_id, event_type])
            conn.commit()
            flash('✅ Event added', 'success')
        except Exception as e:
            flash(f'⚠️ {e}', 'error')

        # Note: Using callproc here too for consistency and safety
        cursor.callproc('GetLifecycleReport', (inst_id,))
        for result in cursor.stored_results():
            timeline = result.fetchall()
            
        selected = inst_id

    conn.close()
    return render_template('instance_detail.html', instances=instances, timeline=timeline, selected=selected)


# -------------------------
# 4) SUPPLIERS & SOURCING PAGE
# -------------------------
@app.route('/suppliers', methods=['GET', 'POST'])
def suppliers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT ComponentID, ComponentName FROM Components")
    components = cursor.fetchall()
    cursor.execute("SELECT MaterialID, MaterialName FROM RawMaterials")
    materials = cursor.fetchall()

    if request.method == 'POST':
        s_id = request.form['supplier_id'].strip()
        s_name = request.form['supplier_name'].strip()
        try:
            cursor.callproc('AddNewSupplier', [s_id, s_name])
            conn.commit()
            flash('✅ Supplier added successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'⚠️ Error adding supplier: {e}', 'error')
        return redirect(url_for('suppliers'))

    cursor.execute("SELECT * FROM Suppliers")
    suppliers = cursor.fetchall()

    cursor.execute("""
        SELECT 
            s.SupplierID, s.SupplierName, c.ComponentName, m.MaterialName
        FROM Suppliers s
        LEFT JOIN Sourcing so ON s.SupplierID = so.SupplierID
        LEFT JOIN Components c ON so.ComponentID = c.ComponentID
        LEFT JOIN RawMaterials m ON so.MaterialID = m.MaterialID
        ORDER BY s.SupplierName
    """)
    sourcing = cursor.fetchall()

    supplier_types = {}
    cursor.execute("""
        SELECT SupplierID,
               SUM(ComponentID IS NOT NULL) AS comp_count,
               SUM(MaterialID IS NOT NULL) AS mat_count
        FROM Sourcing
        GROUP BY SupplierID
    """)
    for row in cursor.fetchall():
        cid = row['SupplierID']
        comp_count = row['comp_count'] or 0
        mat_count = row['mat_count'] or 0
        if comp_count > 0 and mat_count > 0:
            supplier_types[cid] = 'Both'
        elif comp_count > 0:
            supplier_types[cid] = 'Component Supplier'
        elif mat_count > 0:
            supplier_types[cid] = 'Material Supplier'
        else:
            supplier_types[cid] = 'Unknown'

    conn.close()
    return render_template('suppliers.html',
                            suppliers=suppliers,
                            sourcing=sourcing,
                            supplier_types=supplier_types,
                            components=components,
                            materials=materials)


@app.route('/add_sourcing', methods=['POST'])
def add_sourcing():
    conn = get_db_connection()
    cursor = conn.cursor()

    supplier_id = request.form['supplier_id']
    supply_type = request.form['supply_type']
    item_id = request.form['item_id']

    try:
        if supply_type == 'component':
            cursor.execute(
                "INSERT INTO Sourcing (SupplierID, ComponentID, MaterialID) VALUES (%s, %s, NULL)",
                (supplier_id, item_id)
            )
        elif supply_type == 'material':
            cursor.execute(
                "INSERT INTO Sourcing (SupplierID, ComponentID, MaterialID) VALUES (%s, NULL, %s)",
                (supplier_id, item_id)
            )
        else:
            return jsonify({'status': 'error', 'message': 'Invalid supply type'})
        conn.commit()
        return jsonify({'status': 'ok', 'message': 'Sourcing added successfully!'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()


# -------------------------
# 5) COMPONENT COMPOSITION PAGE (FIXED)
# -------------------------
@app.route('/materials', methods=['GET', 'POST'])
def materials():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # --- POST Logic (For *adding* a new material) ---
    if request.method == 'POST':
        comp_id = request.form.get('component_id')
        mat_id = request.form.get('material_id')
        
        # Get weight from the number input (which is synced to the slider)
        weight = request.form.get('weight_num') 

        try:
            cursor.callproc('AddMaterialComposition', [comp_id, mat_id, weight])
            conn.commit()
            flash('✅ Composition added', 'success')
        except Exception as e:
            flash(f'⚠️ {e}', 'error')
        
        # **THE FIX (PRG Pattern):**
        # Redirect back to the GET page for this component.
        # This keeps the URL clean and prevents re-POSTs on refresh.
        conn.close()
        return redirect(url_for('materials', component=comp_id))

    # --- GET Logic (For *viewing* the page) ---
    # This code now runs for all GET requests
    
    # 1. Always fetch dropdown lists
    cursor.execute("SELECT ComponentID, ComponentName FROM Components")
    components = cursor.fetchall()
    cursor.execute("SELECT MaterialID, MaterialName, IsHazardous FROM RawMaterials")
    materials_list = cursor.fetchall()

    # 2. Check if a component is selected in the URL
    # We look for a URL parameter like: /materials?component=c100
    selected_component_id = request.args.get('component') 

    composition_rows = []
    composition_chart_data = {}

    # 3. If a component was selected, fetch its data
    if selected_component_id:
        cursor.execute("""
            SELECT cc.ComponentID, cc.MaterialID, rm.MaterialName, cc.WeightInGrams, rm.IsHazardous
            FROM ComponentComposition cc
            JOIN RawMaterials rm ON cc.MaterialID = rm.MaterialID
            WHERE cc.ComponentID = %s
        """, (selected_component_id,))
        composition_rows = cursor.fetchall()

        # Only build chart data if we have rows
        if composition_rows:
            labels = [r['MaterialName'] for r in composition_rows]
            weights = [float(r['WeightInGrams']) for r in composition_rows]
            composition_chart_data = {'labels': labels, 'weights': weights}

    conn.close()
    
    # 4. Render the template with all the data
    return render_template('materials.html', 
                           components=components, 
                           materials=materials_list,
                           compositions=composition_rows, 
                           selected_component=selected_component_id, # Pass the selected ID
                           composition_chart_data=composition_chart_data)

# -------------------------
# 6) REPORTS / ANALYTICS PAGE (FIXED)
# -------------------------
@app.route('/reports', methods=['GET', 'POST'])
def reports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT InstanceID, SerialNumber FROM ProductInstances")
    instances = cursor.fetchall()
    cursor.execute("SELECT ProductID, ModelName FROM Products")
    products = cursor.fetchall()

    lifecycle_timeline = []
    trace_rows = []
    component_hierarchy = []

    # --- CHANGE 1: Initialize all variables ---
    # We need to define them all here, including the new 'age'
    selected_product_id = None
    selected_instance_id = None  
    selected_instance_serial = None
    selected_product_name = None
    age_in_days = None           
    

    if request.method == 'POST':
        report_type = request.form.get('report_type')

        if report_type == 'lifecycle':
            inst_id = request.form.get('instance_id')
            
            # --- CHANGE 2: Get data for title, age, and sticky dropdown ---
            selected_instance_id = inst_id  # Store this to make dropdown "sticky"

            # Get the serial number AND age
            cursor.execute("""
                SELECT SerialNumber, GetLifecycleAge(InstanceID) AS age
                FROM ProductInstances 
                WHERE InstanceID = %s
            """, (inst_id,))
            
            result = cursor.fetchone()
            if result:
                selected_instance_serial = result['SerialNumber']
                age_in_days = result['age']  # <-- STORE THE AGE
            # --- End Change ---

            # Now, get the timeline
            cursor.callproc('GetLifecycleReport', (inst_id,))
            for result in cursor.stored_results():
                lifecycle_timeline = result.fetchall()

        elif report_type == 'trace':
            selected_product_id = request.form.get('product_id') # Store for sticky dropdown
            
            # Get the product name for the H4 title
            cursor.execute("SELECT ModelName FROM Products WHERE ProductID = %s", (selected_product_id,))
            result = cursor.fetchone()
            if result:
                selected_product_name = result['ModelName']

            # Get the trace data
            cursor.execute("""
                    SELECT 
                        ComponentName, 
                        MaterialName, 
                        WeightInGrams, 
                        RecyclableGrade,
                        CASE 
                            WHEN IsHazardous = 1 THEN 'Yes'
                            ELSE 'No'
                        END AS IsHazardous
                    FROM ProductMaterialPassport
                    WHERE ProductID = %s
                    ORDER BY ComponentName;
                """, (selected_product_id,))
            trace_rows = cursor.fetchall()
        
    cursor.execute("""
        SELECT 
            c.ComponentID,
            c.ComponentName,
            GetComponentSummary(c.ComponentID) AS Summary
        FROM Components c
        WHERE c.ComponentID IN ('c100', 'c200', 'c310');
    """)
    component_hierarchy = cursor.fetchall()

    conn.close()
    
    # --- CHANGE 3: Pass ALL variables to the template ---
    # Your old code was missing the "selected" variables and the new 'age'
    return render_template(
        'reports.html',
        instances=instances,
        products=products,
        lifecycle_timeline=lifecycle_timeline,
        trace_rows=trace_rows,
        component_hierarchy=component_hierarchy,
        
        # Pass all the "selected" data
        selected_instance_serial=selected_instance_serial,
        selected_product_name=selected_product_name,
        selected_instance_id=selected_instance_id,  
        selected_product_id=selected_product_id,
        
        age_in_days=age_in_days  # <-- PASS THE NEW AGE VARIABLE
    )
# -------------------------
# API
# -------------------------
@app.route('/api/products')
def api_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ProductID, ModelName FROM Products")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)


if __name__ == '__main__':
    app.run(debug=True)