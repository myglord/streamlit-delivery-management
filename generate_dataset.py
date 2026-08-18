#!/usr/bin/env python3
"""
Generates delivery_orders.csv — the sample dataset for the Streamlit
Order Delivery Management System (lab10/app.py).

Re-run any time to get a fresh randomized dataset:
    python3 generate_dataset.py
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N = 350

CITIES = ["Lagos", "Abuja", "Nairobi", "Accra", "Kampala"]
CITY_COORDS = {
    "Lagos": (6.5244, 3.3792),
    "Abuja": (9.0765, 7.3986),
    "Nairobi": (-1.2921, 36.8219),
    "Accra": (5.6037, -0.1870),
    "Kampala": (0.3476, 32.5825),
}
RESTAURANTS = [
    "Mama Put Kitchen", "Spice Route", "Green Bowl", "Urban Grill",
    "Golden Wok", "The Pizza Yard", "Ocean Basket", "Burger Barn",
    "Curry Leaf", "Sweet Treats Bakery",
]
CUISINES = ["Local", "Chinese", "Italian", "Indian", "Fast Food", "Continental"]
PAYMENT_METHODS = ["Cash on Delivery", "Card", "Mobile Money", "Wallet"]
DELIVERY_PARTNERS = [
    "Tunde A.", "Amara K.", "Chidi O.", "Fatima B.", "Kwame N.",
    "Ngozi E.", "Samuel T.", "Ruth W.",
]
STATUSES = ["Pending", "Preparing", "Out for Delivery", "Delivered", "Cancelled"]
STATUS_WEIGHTS = [0.08, 0.10, 0.12, 0.65, 0.05]

CUSTOMER_FIRST = ["Ada", "Ife", "John", "Grace", "Musa", "Zainab", "David", "Peace",
                  "Kelechi", "Mary", "Emeka", "Blessing", "Yusuf", "Joy", "Tariq"]
CUSTOMER_LAST = ["Okafor", "Bello", "Mensah", "Otieno", "Abara", "Chukwu", "Adeyemi",
                 "Nwosu", "Kamau", "Osei"]

def make_dataset() -> pd.DataFrame:
    order_ids = np.arange(5001, 5001 + N)
    cities = RNG.choice(CITIES, size=N)
    restaurants = RNG.choice(RESTAURANTS, size=N)
    cuisines = RNG.choice(CUISINES, size=N)
    payment_methods = RNG.choice(PAYMENT_METHODS, size=N, p=[0.35, 0.30, 0.25, 0.10])
    partners = RNG.choice(DELIVERY_PARTNERS, size=N)
    statuses = RNG.choice(STATUSES, size=N, p=STATUS_WEIGHTS)

    order_dates = pd.to_datetime("2026-07-01") + pd.to_timedelta(
        RNG.integers(0, 45, size=N), unit="D"
    )
    order_hours = RNG.integers(8, 23, size=N)

    distance_km = np.round(RNG.gamma(shape=2.0, scale=1.6, size=N) + 0.5, 2)
    item_count = RNG.integers(1, 8, size=N)
    base_price = RNG.uniform(800, 6500, size=N)
    order_amount = np.round(base_price + item_count * RNG.uniform(150, 500, size=N), 2)
    delivery_fee = np.round(300 + distance_km * RNG.uniform(60, 120, size=N), 2)
    discount_percent = RNG.choice([0, 5, 10, 15, 20], size=N, p=[0.4, 0.2, 0.2, 0.15, 0.05])

    prep_time = np.round(RNG.normal(18, 5, size=N).clip(5, 45), 0)
    travel_time = np.round(distance_km * RNG.uniform(3.5, 6.5, size=N), 0)
    estimated_delivery_min = (prep_time + travel_time).astype(int)
    delay_noise = RNG.normal(0, 6, size=N)
    actual_delivery_min = (estimated_delivery_min + delay_noise).clip(8, None).astype(int)
    actual_delivery_min = np.where(statuses == "Delivered", actual_delivery_min, 0)

    customer_names = [
        f"{RNG.choice(CUSTOMER_FIRST)} {RNG.choice(CUSTOMER_LAST)}" for _ in range(N)
    ]
    ratings = np.where(
        statuses == "Delivered",
        np.round(RNG.normal(4.3, 0.6, size=N).clip(1, 5), 1),
        np.nan,
    )

    lat_jitter = RNG.normal(0, 0.05, size=N)
    lon_jitter = RNG.normal(0, 0.05, size=N)
    lat = [CITY_COORDS[c][0] + j for c, j in zip(cities, lat_jitter)]
    lon = [CITY_COORDS[c][1] + j for c, j in zip(cities, lon_jitter)]

    df = pd.DataFrame({
        "order_id": order_ids,
        "customer_name": customer_names,
        "city": cities,
        "restaurant": restaurants,
        "cuisine": cuisines,
        "order_date": order_dates.strftime("%Y-%m-%d"),
        "order_hour": order_hours,
        "item_count": item_count,
        "order_amount": order_amount,
        "discount_percent": discount_percent,
        "delivery_fee": delivery_fee,
        "distance_km": distance_km,
        "payment_method": payment_methods,
        "delivery_partner": partners,
        "status": statuses,
        "estimated_delivery_min": estimated_delivery_min,
        "actual_delivery_min": actual_delivery_min,
        "customer_rating": ratings,
        "lat": np.round(lat, 5),
        "lon": np.round(lon, 5),
    })
    return df


if __name__ == "__main__":
    df = make_dataset()
    df.to_csv("delivery_orders.csv", index=False)
    print(f"Wrote {len(df)} rows to delivery_orders.csv")
