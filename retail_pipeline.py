"""
Retail Intelligence Platform
Author: Hachem Zenati
Stack: Python, Pandas, SQL (SQLite), Scikit-learn, Matplotlib, Excel
Dataset: 50,000 transactions | 3 years | 8 categories | 5 regions
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sqlite3
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_percentage_error
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
print("=" * 60)
print("  RETAIL INTELLIGENCE PLATFORM")
print("  Author: Hachem Zenati")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
# 1. DATA GENERATION — 50,000 transactions, 3 years
# ─────────────────────────────────────────────────────────────
print("\n[1/5] Generating dataset (50,000 transactions)...")

N = 50_000

categories = {
    'Electronics':    {'price': (80,  1200), 'w': 0.15},
    'Fashion':        {'price': (15,   300), 'w': 0.22},
    'Home & Living':  {'price': (20,   500), 'w': 0.16},
    'Sports':         {'price': (25,   450), 'w': 0.12},
    'Beauty':         {'price': (10,   150), 'w': 0.11},
    'Food & Grocery': {'price': (5,     80), 'w': 0.14},
    'Books':          {'price': (8,     60), 'w': 0.05},
    'Toys':           {'price': (10,   200), 'w': 0.05},
}

regions = {
    'North':    0.28,
    'South':    0.22,
    'East':     0.18,
    'West':     0.20,
    'Central':  0.12,
}

channels = {'Online': 0.52, 'In-Store': 0.33, 'Mobile App': 0.15}

# Seasonality weights per month
month_weights = {
    1: 0.70, 2: 0.72, 3: 0.80, 4: 0.85, 5: 0.90, 6: 0.82,
    7: 0.78, 8: 0.75, 9: 0.88, 10: 0.95, 11: 1.40, 12: 1.60
}

dates = pd.date_range('2022-01-01', '2024-12-31', freq='D')
day_w = np.array([month_weights[d.month] for d in dates], dtype=float)
day_w /= day_w.sum()
order_dates = np.random.choice(dates, size=N, p=day_w)

cat_names = list(categories.keys())
cat_w     = [categories[c]['w'] for c in cat_names]
reg_names = list(regions.keys())
reg_w     = list(regions.values())
ch_names  = list(channels.keys())
ch_w      = list(channels.values())

order_cats = np.random.choice(cat_names, size=N, p=cat_w)
order_regs = np.random.choice(reg_names, size=N, p=reg_w)
order_chs  = np.random.choice(ch_names,  size=N, p=ch_w)

# Generate 5,000 unique customers with repeat purchases
n_customers = 5000
customer_ids = np.random.choice([f'CUST-{i:05d}' for i in range(n_customers)], size=N)

prices, qtys = [], []
for cat in order_cats:
    lo, hi = categories[cat]['price']
    prices.append(round(np.random.uniform(lo, hi), 2))
    qtys.append(np.random.choice([1,1,1,2,2,3,4], p=[0.40,0.22,0.15,0.10,0.07,0.04,0.02]))

prices = np.array(prices)
qtys   = np.array(qtys)
gross  = (prices * qtys).round(2)

discount = np.random.choice(
    [0, 0, 0, 0.05, 0.10, 0.15, 0.20, 0.25],
    size=N, p=[0.40, 0.15, 0.10, 0.12, 0.09, 0.07, 0.05, 0.02]
)
net_rev = (gross * (1 - discount)).round(2)
cogs    = (net_rev * np.random.uniform(0.40, 0.60, N)).round(2)
profit  = (net_rev - cogs).round(2)

status = np.random.choice(
    ['Completed', 'Completed', 'Completed', 'Returned', 'Cancelled'],
    size=N, p=[0.76, 0.08, 0.04, 0.07, 0.05]
)

payment = np.random.choice(
    ['Credit Card', 'PayPal', 'Bank Transfer', 'Cash', 'Crypto'],
    size=N, p=[0.38, 0.28, 0.18, 0.12, 0.04]
)

df = pd.DataFrame({
    'order_id':      [f'ORD-{100000+i}' for i in range(N)],
    'customer_id':   customer_ids,
    'order_date':    order_dates,
    'category':      order_cats,
    'region':        order_regs,
    'channel':       order_chs,
    'unit_price':    prices,
    'quantity':      qtys,
    'gross_revenue': gross,
    'discount_pct':  discount,
    'net_revenue':   net_rev,
    'cogs':          cogs,
    'profit':        profit,
    'payment':       payment,
    'status':        status,
})
df['order_date'] = pd.to_datetime(df['order_date'])
df['year']    = df['order_date'].dt.year
df['month']   = df['order_date'].dt.month
df['quarter'] = df['order_date'].dt.to_period('Q').astype(str)
df['ym']      = df['order_date'].dt.to_period('M').astype(str)
df['week']    = df['order_date'].dt.isocalendar().week.astype(int)

df.to_csv('data/transactions.csv', index=False)
print(f"  ✓ {len(df):,} transactions | Revenue: ${df['net_revenue'].sum():,.0f} | Profit: ${df['profit'].sum():,.0f}")

# ─────────────────────────────────────────────────────────────
# 2. SQL ANALYSIS — Advanced queries
# ─────────────────────────────────────────────────────────────
print("\n[2/5] Running SQL analysis...")

conn = sqlite3.connect(':memory:')
df.to_sql('orders', conn, index=False, if_exists='replace')

# Query 1: Monthly revenue with MoM growth (window function style)
monthly = pd.read_sql("""
    SELECT ym,
           ROUND(SUM(net_revenue), 2)  AS revenue,
           ROUND(SUM(profit), 2)       AS profit,
           COUNT(DISTINCT order_id)    AS orders,
           COUNT(DISTINCT customer_id) AS unique_customers,
           ROUND(AVG(net_revenue), 2)  AS avg_order_value,
           ROUND(SUM(profit)*100.0/SUM(net_revenue), 1) AS margin_pct
    FROM orders
    WHERE status = 'Completed'
    GROUP BY ym
    ORDER BY ym
""", conn)

# Query 2: Category deep-dive with rank
cat_perf = pd.read_sql("""
    SELECT category,
           COUNT(DISTINCT order_id)    AS orders,
           COUNT(DISTINCT customer_id) AS customers,
           ROUND(SUM(net_revenue), 2)  AS revenue,
           ROUND(SUM(profit), 2)       AS profit,
           ROUND(AVG(net_revenue), 2)  AS avg_order,
           ROUND(SUM(profit)*100.0/SUM(net_revenue), 1) AS margin_pct,
           ROUND(AVG(discount_pct)*100, 1) AS avg_discount
    FROM orders WHERE status='Completed'
    GROUP BY category
    ORDER BY revenue DESC
""", conn)

# Query 3: Region × Channel matrix
region_channel = pd.read_sql("""
    SELECT region, channel,
           COUNT(*) AS orders,
           ROUND(SUM(net_revenue), 2) AS revenue,
           ROUND(AVG(net_revenue), 2) AS avg_order
    FROM orders WHERE status='Completed'
    GROUP BY region, channel
    ORDER BY revenue DESC
""", conn)

# Query 4: YoY comparison with growth
yoy = pd.read_sql("""
    SELECT year,
           ROUND(SUM(net_revenue), 2)  AS revenue,
           ROUND(SUM(profit), 2)       AS profit,
           COUNT(DISTINCT order_id)    AS orders,
           COUNT(DISTINCT customer_id) AS customers,
           ROUND(AVG(net_revenue), 2)  AS avg_order
    FROM orders WHERE status='Completed'
    GROUP BY year ORDER BY year
""", conn)

# Query 5: Discount impact analysis
disc_impact = pd.read_sql("""
    SELECT CASE
        WHEN discount_pct = 0    THEN '0% (No discount)'
        WHEN discount_pct <= 0.10 THEN '1-10%'
        WHEN discount_pct <= 0.20 THEN '11-20%'
        ELSE '21-25%'
    END AS discount_bucket,
           COUNT(*) AS orders,
           ROUND(AVG(net_revenue), 2) AS avg_revenue,
           ROUND(AVG(profit), 2)      AS avg_profit,
           ROUND(AVG(profit)*100.0/AVG(net_revenue), 1) AS margin_pct
    FROM orders WHERE status='Completed'
    GROUP BY discount_bucket
    ORDER BY avg_profit DESC
""", conn)

# Query 6: Top customers by LTV
top_customers = pd.read_sql("""
    SELECT customer_id,
           COUNT(DISTINCT order_id)   AS total_orders,
           ROUND(SUM(net_revenue), 2) AS lifetime_value,
           ROUND(AVG(net_revenue), 2) AS avg_order,
           MIN(order_date)            AS first_purchase,
           MAX(order_date)            AS last_purchase
    FROM orders WHERE status='Completed'
    GROUP BY customer_id
    ORDER BY lifetime_value DESC
    LIMIT 20
""", conn)

print("  ✓ 6 SQL queries executed (monthly, category, region×channel, YoY, discount, LTV)")

# ─────────────────────────────────────────────────────────────
# 3. RFM SEGMENTATION + K-MEANS CLUSTERING
# ─────────────────────────────────────────────────────────────
print("\n[3/5] Running RFM segmentation & customer clustering...")

snapshot = df['order_date'].max() + pd.Timedelta(days=1)
completed = df[df['status'] == 'Completed']

rfm = completed.groupby('customer_id').agg(
    Recency   = ('order_date',   lambda x: (snapshot - x.max()).days),
    Frequency = ('order_id',     'count'),
    Monetary  = ('net_revenue',  'sum')
).reset_index()

rfm['Monetary'] = rfm['Monetary'].round(2)

# Score 1-5
for col in ['Recency', 'Frequency', 'Monetary']:
    if col == 'Recency':
        rfm[f'{col}_Score'] = pd.qcut(rfm[col], 5, labels=[5,4,3,2,1], duplicates='drop').astype(int)
    else:
        rfm[f'{col}_Score'] = pd.qcut(rfm[col], 5, labels=[1,2,3,4,5], duplicates='drop').astype(int)

rfm['RFM_Score'] = rfm['Recency_Score'] + rfm['Frequency_Score'] + rfm['Monetary_Score']

def segment(row):
    r, f, m = row['Recency_Score'], row['Frequency_Score'], row['Monetary_Score']
    if r >= 4 and f >= 4 and m >= 4: return 'Champions'
    elif r >= 3 and f >= 3:          return 'Loyal Customers'
    elif r >= 4 and f <= 2:          return 'New Customers'
    elif r <= 2 and f >= 3:          return 'At Risk'
    elif r <= 2 and f <= 2:          return 'Lost'
    else:                            return 'Potential Loyalists'

rfm['Segment'] = rfm.apply(segment, axis=1)

# K-Means clustering (4 clusters)
scaler = StandardScaler()
X = scaler.fit_transform(rfm[['Recency', 'Frequency', 'Monetary']])
km = KMeans(n_clusters=4, random_state=42, n_init=10)
rfm['Cluster'] = km.fit_predict(X)

cluster_labels = {
    rfm.groupby('Cluster')['Monetary'].mean().idxmax(): 'High Value',
    rfm.groupby('Cluster')['Frequency'].mean().idxmax(): 'Frequent Buyers',
    rfm.groupby('Cluster')['Recency'].mean().idxmin(): 'Recent Buyers',
}
rfm['Cluster_Name'] = rfm['Cluster'].map(
    lambda x: cluster_labels.get(x, 'Occasional Buyers')
)

seg_summary = rfm.groupby('Segment').agg(
    Customers=('customer_id','count'),
    Avg_Recency=('Recency','mean'),
    Avg_Frequency=('Frequency','mean'),
    Avg_LTV=('Monetary','mean')
).round(1).reset_index().sort_values('Avg_LTV', ascending=False)

print(f"  ✓ RFM segmentation complete — {rfm['Segment'].nunique()} segments, {len(rfm):,} customers")
print(f"  ✓ K-Means clustering — 4 clusters identified")

# ─────────────────────────────────────────────────────────────
# 4. DEMAND FORECASTING — Linear Regression per category
# ─────────────────────────────────────────────────────────────
print("\n[4/5] Running demand forecasting (next 6 months)...")

monthly['month_num'] = range(len(monthly))
forecasts = {}

# Per-category monthly revenue
cat_monthly = completed.groupby(['ym', 'category'])['net_revenue'].sum().reset_index()
cat_monthly['month_num'] = cat_monthly.groupby('category').cumcount()

forecast_rows = []
mape_scores   = {}

for cat in cat_names:
    sub = cat_monthly[cat_monthly['category'] == cat].copy()
    if len(sub) < 12:
        continue
    X_tr = sub[['month_num']].values
    y_tr = sub['net_revenue'].values
    model = LinearRegression()
    model.fit(X_tr, y_tr)
    y_pred = model.predict(X_tr)
    mape   = mean_absolute_percentage_error(y_tr, y_pred)
    mape_scores[cat] = round(mape * 100, 1)
    last_m = sub['month_num'].max()
    last_ym = pd.Period(sub['ym'].iloc[-1], freq='M')
    for i in range(1, 7):
        fut_m  = last_m + i
        fut_ym = str(last_ym + i)
        pred   = max(0, model.predict([[fut_m]])[0])
        forecast_rows.append({'category': cat, 'ym': fut_ym,
                               'forecasted_revenue': round(pred, 2),
                               'month_offset': i})

forecast_df = pd.DataFrame(forecast_rows)
print(f"  ✓ Forecasted next 6 months for {len(cat_names)} categories")
print(f"  ✓ Avg MAPE: {np.mean(list(mape_scores.values())):.1f}%")

# ─────────────────────────────────────────────────────────────
# 5. DASHBOARD — 12 panels
# ─────────────────────────────────────────────────────────────
print("\n[5/5] Building 12-panel executive dashboard...")

BG   = '#0d1117'; BG2 = '#161b22'; BG3 = '#1f2937'
BLU  = '#58a6ff'; GRN = '#26a641'; RED = '#f85149'
GOLD = '#ffd700'; PRP = '#a371f7'; TEA = '#39d353'
CYN  = '#56d4dd'; ORG = '#f0883e'; WHT = '#e6edf3'; GRAY = '#8b949e'

COLORS = [BLU, PRP, GOLD, GRN, CYN, ORG, RED, TEA]

fig = plt.figure(figsize=(22, 16), facecolor=BG)
fig.suptitle('Retail Intelligence Platform  |  Executive Dashboard  |  2022–2024  |  50,000 Transactions',
             fontsize=18, fontweight='bold', color=WHT, y=0.985)
gs = gridspec.GridSpec(4, 4, figure=fig,
                       hspace=0.52, wspace=0.38,
                       left=0.04, right=0.97, top=0.95, bottom=0.05)

def sax(ax, title=''):
    ax.set_facecolor(BG2)
    for sp in ax.spines.values():
        sp.set_color('#30363d'); sp.set_linewidth(0.5)
    ax.tick_params(colors=GRAY, labelsize=8)
    if title:
        ax.set_title(title, color=WHT, fontsize=9, pad=7, fontweight='bold')

# ── Panel 1: KPI Cards ─────────────────────────────────────
ax0 = fig.add_subplot(gs[0, 0])
ax0.set_facecolor(BG); ax0.axis('off')
comp = df[df['status']=='Completed']
kpis = [
    ('Total Revenue',      f"${comp['net_revenue'].sum()/1e6:.2f}M",    BLU),
    ('Total Profit',       f"${comp['profit'].sum()/1e6:.2f}M",         GRN),
    ('Total Orders',       f"{comp['order_id'].nunique():,}",            GOLD),
    ('Unique Customers',   f"{comp['customer_id'].nunique():,}",         PRP),
]
for i,(lbl,val,col) in enumerate(kpis):
    y0 = 0.82 - i*0.22
    r  = plt.Rectangle((0.04, y0-0.09), 0.92, 0.18,
                        transform=ax0.transAxes, facecolor=BG2,
                        edgecolor='#30363d', linewidth=0.5)
    ax0.add_patch(r)
    ax0.text(0.10, y0+0.02, lbl, transform=ax0.transAxes, fontsize=8,  color=GRAY, va='center')
    ax0.text(0.10, y0-0.06, val, transform=ax0.transAxes, fontsize=13, color=col,  va='center', fontweight='bold')

# ── Panel 2: Monthly Revenue trend ────────────────────────
ax1 = fig.add_subplot(gs[0, 1:3])
sax(ax1, 'Monthly Revenue vs Profit (36 months)')
x1 = range(len(monthly))
ax1.bar(x1, monthly['revenue'], color=BLU, alpha=0.65, label='Revenue', width=0.8)
ax1.bar(x1, monthly['profit'],  color=GRN, alpha=0.85, label='Profit',  width=0.8)
ax1.set_xticks(list(x1)[::4])
ax1.set_xticklabels(monthly['ym'].iloc[::4], rotation=35, ha='right', fontsize=7)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'${v/1000:.0f}k'))
ax1.legend(fontsize=8, facecolor=BG3, edgecolor='#30363d', labelcolor=WHT)

# ── Panel 3: Category Pie ──────────────────────────────────
ax2 = fig.add_subplot(gs[0, 3])
sax(ax2, 'Revenue Share by Category')
wedges, texts, autos = ax2.pie(
    cat_perf['revenue'], labels=cat_perf['category'],
    autopct='%1.0f%%', colors=COLORS,
    pctdistance=0.78, startangle=90,
    wedgeprops=dict(edgecolor=BG, linewidth=1.2))
for t in texts: t.set_color(GRAY); t.set_fontsize(6.5)
for t in autos: t.set_color(BG);   t.set_fontsize(7); t.set_fontweight('bold')

# ── Panel 4: Region × Channel Heatmap ─────────────────────
ax3 = fig.add_subplot(gs[1, 0])
sax(ax3, 'Revenue: Region × Channel')
pivot = region_channel.pivot_table(
    index='region', columns='channel', values='revenue', fill_value=0)
im = ax3.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
ax3.set_xticks(range(len(pivot.columns))); ax3.set_xticklabels(pivot.columns, fontsize=7, color=GRAY)
ax3.set_yticks(range(len(pivot.index)));   ax3.set_yticklabels(pivot.index,   fontsize=7, color=GRAY)
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        ax3.text(j, i, f"${pivot.values[i,j]/1000:.0f}k",
                 ha='center', va='center', fontsize=6.5, color='black', fontweight='bold')

# ── Panel 5: Category Margin ──────────────────────────────
ax4 = fig.add_subplot(gs[1, 1])
sax(ax4, 'Profit Margin % by Category')
cm = cat_perf.sort_values('margin_pct')
col_m = [GRN if v >= 45 else (GOLD if v >= 38 else RED) for v in cm['margin_pct']]
ax4.barh(cm['category'], cm['margin_pct'], color=col_m, alpha=0.85)
for i, v in enumerate(cm['margin_pct']):
    ax4.text(v+0.3, i, f'{v:.1f}%', va='center', color=WHT, fontsize=8)
ax4.set_xlabel('Margin %', color=GRAY, fontsize=8)

# ── Panel 6: YoY Grouped Bar ──────────────────────────────
ax5 = fig.add_subplot(gs[1, 2])
sax(ax5, 'Year-over-Year Performance')
x5 = np.arange(len(yoy))
ax5.bar(x5-0.2, yoy['revenue']/1e6, width=0.35, color=BLU, alpha=0.85, label='Revenue (M$)')
ax5.bar(x5+0.2, yoy['profit']/1e6,  width=0.35, color=GRN, alpha=0.85, label='Profit (M$)')
ax5.set_xticks(x5); ax5.set_xticklabels(yoy['year'].astype(str), color=GRAY)
ax5.set_ylabel('M$', color=GRAY, fontsize=8)
ax5.legend(fontsize=7.5, facecolor=BG3, edgecolor='#30363d', labelcolor=WHT)
if len(yoy) >= 2:
    g = (yoy['revenue'].iloc[-1] - yoy['revenue'].iloc[0]) / yoy['revenue'].iloc[0] * 100
    ax5.set_title(f'3Y Revenue Growth: +{g:.1f}%', color=GOLD, fontsize=9, pad=7, fontweight='bold')

# ── Panel 7: RFM Segment distribution ────────────────────
ax6 = fig.add_subplot(gs[1, 3])
sax(ax6, 'Customer RFM Segments')
seg_c = rfm['Segment'].value_counts()
seg_colors = {'Champions':BLU,'Loyal Customers':GRN,'Potential Loyalists':CYN,
              'New Customers':GOLD,'At Risk':ORG,'Lost':RED}
cols_seg = [seg_colors.get(s, GRAY) for s in seg_c.index]
ax6.barh(seg_c.index, seg_c.values, color=cols_seg, alpha=0.85)
for i,v in enumerate(seg_c.values):
    ax6.text(v+5, i, str(v), va='center', color=WHT, fontsize=8)
ax6.set_xlabel('Customers', color=GRAY, fontsize=8)

# ── Panel 8: K-Means Scatter (R vs M) ────────────────────
ax7 = fig.add_subplot(gs[2, 0])
sax(ax7, 'Customer Clustering (K-Means, k=4)')
cluster_cols = [BLU, GOLD, GRN, RED]
for cl in range(4):
    sub = rfm[rfm['Cluster'] == cl]
    ax7.scatter(sub['Recency'], sub['Monetary'],
                c=cluster_cols[cl], alpha=0.35, s=8,
                label=sub['Cluster_Name'].iloc[0])
ax7.set_xlabel('Recency (days)', color=GRAY, fontsize=8)
ax7.set_ylabel('Monetary ($)', color=GRAY, fontsize=8)
ax7.legend(fontsize=7, facecolor=BG3, edgecolor='#30363d', labelcolor=WHT)

# ── Panel 9: Demand Forecast ──────────────────────────────
ax8 = fig.add_subplot(gs[2, 1:3])
sax(ax8, 'Demand Forecast — Next 6 Months by Category')
for i, cat in enumerate(cat_names[:6]):
    hist = cat_monthly[cat_monthly['category']==cat].copy()
    fwd  = forecast_df[forecast_df['category']==cat].copy()
    x_h  = range(len(hist))
    x_f  = range(len(hist)-1, len(hist)+len(fwd))
    y_f  = [hist['net_revenue'].iloc[-1]] + list(fwd['forecasted_revenue'])
    ax8.plot(x_h, hist['net_revenue'], color=COLORS[i], alpha=0.6, linewidth=1)
    ax8.plot(x_f, y_f, color=COLORS[i], alpha=1.0, linewidth=1.5,
             linestyle='--', label=cat)
ax8.axvline(x=len(hist)-1, color=GRAY, linewidth=0.8, linestyle=':', alpha=0.7)
ax8.text(len(hist), ax8.get_ylim()[1]*0.9, ' Forecast →',
         color=GRAY, fontsize=8, va='top')
ax8.legend(fontsize=7, facecolor=BG3, edgecolor='#30363d', labelcolor=WHT, ncol=2)
ax8.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'${v/1000:.0f}k'))

# ── Panel 10: Discount Impact ────────────────────────────
ax9 = fig.add_subplot(gs[2, 3])
sax(ax9, 'Discount Impact on Profit')
dc = disc_impact.copy()
col_d = [GRN if v >= dc['avg_profit'].median() else RED for v in dc['avg_profit']]
ax9.bar(range(len(dc)), dc['avg_profit'], color=col_d, alpha=0.85, width=0.6)
ax9.set_xticks(range(len(dc)))
ax9.set_xticklabels(dc['discount_bucket'], fontsize=7, color=GRAY, rotation=15, ha='right')
ax9.set_ylabel('Avg Profit ($)', color=GRAY, fontsize=8)
for i,v in enumerate(dc['avg_profit']):
    ax9.text(i, v+0.5, f'${v:.0f}', ha='center', color=WHT, fontsize=7.5)

# ── Panel 11: Channel mix trend ──────────────────────────
ax10 = fig.add_subplot(gs[3, :2])
sax(ax10, 'Revenue by Channel — Monthly Trend')
ch_monthly = completed.groupby(['ym','channel'])['net_revenue'].sum().unstack(fill_value=0)
x10 = range(len(ch_monthly))
bottom = np.zeros(len(ch_monthly))
ch_colors = [BLU, GRN, PRP]
for j, ch in enumerate(ch_monthly.columns):
    ax10.bar(x10, ch_monthly[ch], bottom=bottom, color=ch_colors[j],
             alpha=0.85, label=ch, width=0.85)
    bottom += ch_monthly[ch].values
ax10.set_xticks(list(x10)[::4])
ax10.set_xticklabels(ch_monthly.index[::4], rotation=35, ha='right', fontsize=7)
ax10.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'${v/1000:.0f}k'))
ax10.legend(fontsize=8, facecolor=BG3, edgecolor='#30363d', labelcolor=WHT)

# ── Panel 12: Top 10 LTV customers ───────────────────────
ax11 = fig.add_subplot(gs[3, 2:])
sax(ax11, 'Top 10 Customers by Lifetime Value')
top10 = top_customers.head(10)
x11   = range(len(top10))
bars  = ax11.bar(x11, top10['lifetime_value'], color=GOLD, alpha=0.85, width=0.7)
ax11.set_xticks(x11)
ax11.set_xticklabels(top10['customer_id'], rotation=40, ha='right', fontsize=7, color=GRAY)
ax11.set_ylabel('Lifetime Value ($)', color=GRAY, fontsize=8)
ax11.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'${v/1000:.0f}k'))
for bar, orders in zip(bars, top10['total_orders']):
    ax11.text(bar.get_x()+bar.get_width()/2, bar.get_height()+10,
              f'{orders} orders', ha='center', fontsize=6.5, color=GRAY)

plt.savefig('retail_dashboard.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
print("  ✓ 12-panel dashboard saved!")

# ─────────────────────────────────────────────────────────────
# 6. EXCEL EXPORT — 8 sheets
# ─────────────────────────────────────────────────────────────
print("\n[6/6] Exporting Excel workbook (8 sheets)...")

with pd.ExcelWriter('retail_report.xlsx', engine='openpyxl') as writer:
    df.head(2000).to_excel(writer,         sheet_name='Raw Data (sample)',      index=False)
    monthly.to_excel(writer,               sheet_name='Monthly Revenue',        index=False)
    cat_perf.to_excel(writer,              sheet_name='Category Performance',   index=False)
    region_channel.to_excel(writer,        sheet_name='Region × Channel',       index=False)
    yoy.to_excel(writer,                   sheet_name='YoY Comparison',         index=False)
    rfm.head(1000).to_excel(writer,        sheet_name='RFM Segmentation',       index=False)
    seg_summary.to_excel(writer,           sheet_name='Segment Summary',        index=False)
    forecast_df.to_excel(writer,           sheet_name='Demand Forecast',        index=False)

print("  ✓ Excel workbook saved (8 sheets)!")

print("\n" + "=" * 60)
print("  ALL DONE!")
print(f"  Revenue:   ${comp['net_revenue'].sum()/1e6:.2f}M")
print(f"  Profit:    ${comp['profit'].sum()/1e6:.2f}M")
print(f"  Customers: {rfm['customer_id'].nunique():,}")
print(f"  Champions: {(rfm['Segment']=='Champions').sum():,} customers")
print("=" * 60)
conn.close()
