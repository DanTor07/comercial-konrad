from django.http import JsonResponse


def get_simulated_sales(request):
    """
    Simulated REST API to consult sales data.
    """
    # In a real scenario, we would use the domain services
    data = [
        {"id": 1, "producto": "Producto A", "cantidad": 10, "total": 100.0, "fecha": "2024-03-09"},
        {"id": 2, "producto": "Producto B", "cantidad": 5, "total": 150.0, "fecha": "2024-03-09"},
    ]
    return JsonResponse({"status": "success", "data": data})

def get_simulated_sellers(request):
    """
    Simulated REST API to consult sellers data.
    """
    data = [
        {"id": 1, "nombre": "Vendedor 1", "email": "v1@example.com", "estado": "Activo"},
        {"id": 2, "nombre": "Vendedor 2", "email": "v2@example.com", "estado": "Pendiente"},
    ]
    return JsonResponse({"status": "success", "data": data})
