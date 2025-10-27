@app.route('/api/admin/reservations', methods=['GET'])
@jwt_required()
def get_admin_reservations():
    if not is_admin():
        return jsonify({'error': 'Unauthorized access'}), 403
    
    location_service = LocationService()
    reservations = location_service.get_all_reservations()
    return jsonify(reservations)