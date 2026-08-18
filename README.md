# 🛵 Domain Order Delivery Management System

An interactive Streamlit app for managing and analyzing food-delivery orders.
Built as a course project to demonstrate Streamlit widgets, data visualization,
user interaction, and cloud deployment.

## Features / pages

| Page | What it demonstrates |
|---|---|
| 🏠 **Home** | KPI metrics (`st.metric`), bar & pie charts, filtered recent-orders table |
| 📦 **Orders** | Search (`st.text_input`), sort (`st.selectbox`), inline status editing (`st.data_editor`), CSV export (`st.download_button`) |
| ➕ **New Order** | Full input form (`st.form`) — text, selectbox, radio, slider, number, date, checkbox |
| 🚚 **Track Delivery** | Single-order lookup, progress bar, live status advance button, `st.map` |
| 📊 **Analytics** | Tabbed Plotly charts — bar, line, pie, histogram, scatter, box plot, choropleth-style map |

All pages respond to the shared **sidebar filters** (city, status, date range).

## Files

- [`app.py`](app.py) — the Streamlit application
- [`requirements.txt`](requirements.txt) — pinned dependencies
- [`generate_dataset.py`](generate_dataset.py) — regenerates the sample dataset
- [`delivery_orders.csv`](delivery_orders.csv) — sample dataset (350 synthetic orders)

## Dataset

`delivery_orders.csv` has 350 synthetic orders across 5 cities (Lagos, Abuja,
Nairobi, Accra, Kampala) with columns: `order_id, customer_name, city,
restaurant, cuisine, order_date, order_hour, item_count, order_amount,
discount_percent, delivery_fee, distance_km, payment_method,
delivery_partner, status, estimated_delivery_min, actual_delivery_min,
customer_rating, lat, lon`.

Regenerate with a new random seed any time:

```bash
python3 generate_dataset.py
```

Edits made inside the app (status changes, new orders) live only in that
browser session's memory — the CSV on disk is never modified.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## Deploy to GitHub + Streamlit Community Cloud

1. **Create a GitHub repo** (from this `lab10/` folder):

   ```bash
   git init
   git add app.py requirements.txt generate_dataset.py delivery_orders.csv README.md .gitignore
   git commit -m "Order delivery management Streamlit app"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
   - Click **"New app"** → pick your repo, branch `main`, main file path `app.py`.
   - Click **Deploy**. The first build takes 1–3 minutes.
   - Your app will be live at `https://<something>.streamlit.app`.

3. **Update this README** with your actual GitHub repo link and the live
   Streamlit Cloud URL once deployed, for your submission.

## Screenshots for submission

Run the app locally (or open your deployed Streamlit Cloud URL) and capture:

- **Home page** — the KPI dashboard
- At least 2–3 **output pages** — e.g. the Orders table, the New Order
  confirmation, the Track Delivery progress view, or an Analytics chart

On macOS: `Cmd+Shift+4` then drag to select the browser window.
On Windows: `Win+Shift+S`. Save them into a `screenshots/` folder alongside
`app.py` before submitting.

## Submission checklist

- [x] `app.py`
- [x] `requirements.txt`
- [ ] GitHub repository link
- [ ] Streamlit Cloud app URL
- [x] Sample dataset (`delivery_orders.csv`)
- [ ] Screenshots (Home page + output pages)
