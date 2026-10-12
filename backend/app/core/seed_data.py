import json
from pathlib import Path
from datetime import datetime, date, time
from app.core.database import sync_engine, SyncSessionLocal, Base
from app.models.fleet import Depot, Vehicle, Driver, DriverAssignment, ChargingStation
from app.models.orders import Customer, DeliveryRequest, Package

def seed_database():
    print("[Seed] Creating all database tables...")
    Base.metadata.create_all(bind=sync_engine)

    session = SyncSessionLocal()
    try:
        # Check if already seeded
        if session.query(Depot).count() > 0:
            print("[Seed] Database already seeded. Skipping initial seed.")
            return

        print("[Seed] Loading network and orders data...")
        network_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sample_network.json"
        orders_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sample_orders.json"

        with open(network_path, "r") as f:
            network_data = json.load(f)
        
        with open(orders_path, "r") as f:
            orders_data = json.load(f)

        # 1. Seed Depots and Charging Stations from network_data
        depot_map = {}
        for node in network_data["nodes"]:
            if node["type"] == "depot":
                depot = Depot(
                    id=node["id"] + 1, # 1-based in DB
                    name=node["name"],
                    latitude=node["lat"],
                    longitude=node["lon"],
                    address=f"{node['name']}, Metro Hub",
                    operating_hours="07:00-21:00"
                )
                session.add(depot)
                session.flush()
                depot_map[node["id"]] = depot.id
            elif node["type"] == "charging":
                station = ChargingStation(
                    name=node["name"],
                    latitude=node["lat"],
                    longitude=node["lon"],
                    charger_type="DC_Fast_100kW",
                    charging_rate_kw=100.0,
                    cost_per_kwh=0.25,
                    is_available=True
                )
                session.add(station)

        session.commit()
        print(f"[Seed] Created {len(depot_map)} depots and charging stations.")

        # 2. Seed Heterogeneous Vehicles
        depot_ids = list(depot_map.values())
        vehicles = [
            Vehicle(
                depot_id=depot_ids[0],
                license_plate="DL-01-AB-1001",
                vehicle_type="van",
                max_weight_kg=1200.0,
                max_volume_m3=9.0,
                max_range_km=350.0,
                cost_per_km=1.20,
                cost_per_hour=22.0,
                is_electric=False,
                battery_capacity_kwh=0.0,
                current_battery_kwh=0.0,
                emissions_factor_g_co2_per_km=155.0,
                is_available=True
            ),
            Vehicle(
                depot_id=depot_ids[0],
                license_plate="DL-01-EV-2002",
                vehicle_type="ev_van",
                max_weight_kg=900.0,
                max_volume_m3=7.0,
                max_range_km=220.0,
                cost_per_km=0.75,
                cost_per_hour=20.0,
                is_electric=True,
                battery_capacity_kwh=75.0,
                current_battery_kwh=75.0,
                emissions_factor_g_co2_per_km=0.0,
                is_available=True
            ),
            Vehicle(
                depot_id=depot_ids[1] if len(depot_ids) > 1 else depot_ids[0],
                license_plate="DL-02-TR-3003",
                vehicle_type="truck",
                max_weight_kg=3000.0,
                max_volume_m3=22.0,
                max_range_km=500.0,
                cost_per_km=2.10,
                cost_per_hour=35.0,
                is_electric=False,
                battery_capacity_kwh=0.0,
                current_battery_kwh=0.0,
                emissions_factor_g_co2_per_km=280.0,
                is_available=True
            ),
            Vehicle(
                depot_id=depot_ids[2] if len(depot_ids) > 2 else depot_ids[0],
                license_plate="DL-03-EV-4004",
                vehicle_type="ev_van",
                max_weight_kg=800.0,
                max_volume_m3=6.0,
                max_range_km=180.0,
                cost_per_km=0.70,
                cost_per_hour=20.0,
                is_electric=True,
                battery_capacity_kwh=60.0,
                current_battery_kwh=60.0,
                emissions_factor_g_co2_per_km=0.0,
                is_available=True
            ),
        ]
        session.add_all(vehicles)
        session.commit()
        print(f"[Seed] Created {len(vehicles)} heterogeneous fleet vehicles.")

        # 3. Seed Drivers
        drivers = [
            Driver(full_name="Rajesh Kumar", license_number="DL-COMM-8910", max_shift_hours=8.0, hourly_rate=22.0),
            Driver(full_name="Amit Sharma", license_number="DL-COMM-7721", max_shift_hours=8.0, hourly_rate=20.0),
            Driver(full_name="Vikram Singh", license_number="DL-COMM-6532", max_shift_hours=9.0, hourly_rate=24.0),
            Driver(full_name="Sanjay Verma", license_number="DL-COMM-4319", max_shift_hours=8.0, hourly_rate=20.0)
        ]
        session.add_all(drivers)
        session.commit()
        print(f"[Seed] Created {len(drivers)} certified drivers.")

        # 4. Seed Customers, Delivery Requests, and Packages
        today = date.today()
        for ord_info in orders_data["orders"]:
            customer = Customer(
                name=ord_info["customer_name"],
                contact_email=f"contact@{ord_info['customer_name'].lower().replace(' ', '')}.com",
                latitude=ord_info["latitude"],
                longitude=ord_info["longitude"],
                address=ord_info["address"]
            )
            session.add(customer)
            session.flush()

            # Compute datetime windows
            start_h = int(ord_info["window_start_hour"])
            start_m = int((ord_info["window_start_hour"] - start_h) * 60)
            end_h = int(ord_info["window_end_hour"])
            end_m = int((ord_info["window_end_hour"] - end_h) * 60)

            dt_start = datetime.combine(today, time(start_h, start_m))
            dt_end = datetime.combine(today, time(end_h, end_m))

            deliv_req = DeliveryRequest(
                customer_id=customer.id,
                depot_id=depot_ids[0], # Primary default depot
                window_start=dt_start,
                window_end=dt_end,
                priority=ord_info["priority"],
                service_time_min=ord_info["service_time_min"],
                status="pending"
            )
            session.add(deliv_req)
            session.flush()

            for pkg in ord_info["packages"]:
                package = Package(
                    delivery_request_id=deliv_req.id,
                    weight_kg=pkg["weight_kg"],
                    volume_m3=pkg["volume_m3"],
                    fragile=pkg.get("fragile", False),
                    requires_cold_chain=pkg.get("requires_cold_chain", False),
                    tracking_code=f"TRK-{deliv_req.id:04d}-{pkg['weight_kg']:.0f}"
                )
                session.add(package)

        session.commit()
        print(f"[Seed] Successfully seeded {len(orders_data['orders'])} delivery orders and packages.")

    except Exception as e:
        session.rollback()
        print(f"[Seed] Error seeding database: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
