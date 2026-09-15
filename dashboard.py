import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

# --- CONFIG & LAYOUT ---
st.set_page_config(
    page_title="Dashboard Analisis Data Penjualan",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #f0f2f5; }
    .metric-box { background-color: white; padding: 16px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }
    .callout-cyan { background-color: #00838f; color: white; padding: 16px; border-radius: 12px; margin-bottom: 12px; }
    .callout-dark { background-color: #263238; color: white; padding: 16px; border-radius: 12px; margin-bottom: 12px; }
    .callout-pink { background-color: #e91e63; color: white; padding: 16px; border-radius: 12px; margin-bottom: 12px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background-color: #263238; color: white; padding: 15px 25px; border-radius: 12px; margin-bottom: 20px;">
    <h2 style="margin:0; font-size: 24px;">📊 Dashboard Analisis Data Penjualan</h2>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR (UPLOAD FILE & PILIH SHEET) ---
with st.sidebar:
    st.header("📁 Sumber Data")
    uploaded_file = st.file_uploader("Upload Excel (.xlsx) / CSV", type=["xlsx", "csv"])

@st.cache_data
def load_excel_data(file):
    if file is not None:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            xls = pd.ExcelFile(file)
            # Selalu utamakan sheet transaksi jika ada
            sheet_target = 'Data Transaksi ' if 'Data Transaksi ' in xls.sheet_names else xls.sheet_names[0]
            df = pd.read_excel(file, sheet_name=sheet_target)
    else:
        # Fallback dummy jika belum upload file
        dates = pd.date_range(start='2021-01-01', end='2022-12-31', freq='D')
        n = 730
        df = pd.DataFrame({
            'TANGGAL': np.random.choice(dates, n),
            'NAMA PRODUK': np.random.choice(['Pocky', 'Golda Coffee', 'Nyam-nyam'], n),
            'KATEGORI': np.random.choice(['Makanan', 'Minuman'], n),
            'JENIS PENJUALAN': np.random.choice(['Eceran', 'Grosir'], n),
            'METODE PEMBAYARAN': np.random.choice(['Cash', 'Kredit'], n),
            'QTY': np.random.randint(1, 10, n),
            'HARGA JUAL': np.random.choice([15000, 25000], n),
            'TOTAL HARGA JUAL': np.random.randint(15000, 100000, n),
            'TOTAL HARGA BELI': np.random.randint(10000, 80000, n)
        })
    
    # Bersihkan baris kosong
    df = df.dropna(subset=['TANGGAL'])
    
    # Format tanggal & ekstrak Tahun/Bulan
    df['TANGGAL'] = pd.to_datetime(df['TANGGAL'])
    df['Tahun'] = df['TANGGAL'].dt.year.astype(int)
    df['Bulan'] = df['TANGGAL'].dt.month.astype(int)
    
    # Hitung nilai total & profit jika belum ada
    if 'TOTAL HARGA JUAL' not in df.columns and 'QTY' in df.columns and 'HARGA JUAL' in df.columns:
        df['TOTAL HARGA JUAL'] = df['QTY'] * df['HARGA JUAL']
        
    if 'TOTAL HARGA BELI' in df.columns and 'TOTAL HARGA JUAL' in df.columns:
        df['Profit'] = df['TOTAL HARGA JUAL'] - df['TOTAL HARGA BELI']
    elif 'HARGA JUAL' in df.columns and 'HARGA BELI' in df.columns and 'QTY' in df.columns:
        df['Profit'] = (df['HARGA JUAL'] - df['HARGA BELI']) * df['QTY']
    else:
        df['Profit'] = df['TOTAL HARGA JUAL'] * 0.19

    return df

df = load_excel_data(uploaded_file)

# --- SIDEBAR FILTERS (DIPERBAIKI AGAR INTERAKTIF & BISA DIKLIK) ---
with st.sidebar:
    st.markdown("---")
    st.subheader("🔍 Filter Data")
    
    # Filter Tahun
    all_years = sorted(df['Tahun'].unique().tolist())
    selected_tahun = st.multiselect("Pilih Tahun:", options=all_years, default=all_years)

    # Filter Metode Pembayaran
    pay_col = 'METODE PEMBAYARAN' if 'METODE PEMBAYARAN' in df.columns else 'Pembayaran'
    all_pay = sorted(df[pay_col].dropna().unique().tolist())
    selected_pay = st.multiselect("Pilih Pembayaran:", options=all_pay, default=all_pay)

    # Filter Bulan
    bulan_dict = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
    available_months = sorted(df['Bulan'].unique().tolist())
    selected_bulan = st.multiselect(
        "Pilih Bulan:", 
        options=available_months, 
        format_func=lambda x: bulan_dict.get(x, str(x)), 
        default=available_months
    )

# Terapkan Filter ke DataFrame
df_f = df[
    df['Tahun'].isin(selected_tahun) & 
    df[pay_col].isin(selected_pay) & 
    df['Bulan'].isin(selected_bulan)
]

# --- MAIN LAYOUT 3 KOLOM ---
col_left_panel, col_main, col_right_panel = st.columns([1.2, 5, 1.2])

prod_col = 'NAMA PRODUK' if 'NAMA PRODUK' in df.columns else 'Produk'
cat_col = 'KATEGORI' if 'KATEGORI' in df.columns else 'Kategori'
jenis_col = 'JENIS PENJUALAN' if 'JENIS PENJUALAN' in df.columns else 'Jenis_Penjualan'
rev_col = 'TOTAL HARGA JUAL' if 'TOTAL HARGA JUAL' in df.columns else 'Total_Penjualan'
qty_col = 'QTY' if 'QTY' in df.columns else 'Qty'

with col_left_panel:
    if not df_f.empty:
        top_prod = df_f.groupby(prod_col)[qty_col].sum().idxmax()
        top_prod_qty = df_f.groupby(prod_col)[qty_col].sum().max()
    else:
        top_prod, top_prod_qty = "N/A", 0
    st.markdown(f'<div class="callout-cyan"><small>Produk Terlaris</small><h4>{top_prod}</h4><h2>{top_prod_qty:,}</h2><small>Pcs</small></div>', unsafe_allow_html=True)

    if not df_f.empty:
        top_cat = df_f.groupby(cat_col)[rev_col].sum().idxmax()
        top_cat_val = df_f.groupby(cat_col)[rev_col].sum().max()
    else:
        top_cat, top_cat_val = "N/A", 0
    st.markdown(f'<div class="callout-dark"><small>Kategori Terlaris</small><h4>{top_cat}</h4><h3>Rp {top_cat_val/1e6:.1f} jt</h3></div>', unsafe_allow_html=True)

    st.markdown('<div class="callout-pink"><h4 style="margin:0 0 10px 0; font-size:15px;">Kontribusi Nilai Penjualan</h4>', unsafe_allow_html=True)
    if not df_f.empty:
        cat_contrib = df_f.groupby(cat_col)[rev_col].sum()
        tot_rev_all = cat_contrib.sum() if cat_contrib.sum() > 0 else 1
        for c, v in cat_contrib.items():
            st.markdown(f"<div style='display:flex; justify-content:space-between; font-size:13px;'><span>{c}</span><b>{(v/tot_rev_all)*100:.0f}%</b></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    m1, m2, m3 = st.columns(3)
    tot_penjualan = df_f[rev_col].sum() if not df_f.empty else 0
    tot_profit = df_f['Profit'].sum() if not df_f.empty else 0
    tot_qty = df_f[qty_col].sum() if not df_f.empty else 0
    
    profit_pct = (tot_profit / tot_penjualan * 100) if tot_penjualan > 0 else 0

    m1.markdown(f'<div class="metric-box"><small>Total Penjualan</small><h2>{tot_penjualan:,.0f}</h2></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-box"><small>Total Profit</small><h2>{tot_profit:,.0f}</h2><small style="color:green;">{profit_pct:.1f}%</small></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-box"><small>Total Produk Terjual</small><h2>{tot_qty:,.0f}</h2><small>Pcs</small></div>', unsafe_allow_html=True)

    st.write("")
    c_graf1, c_graf2 = st.columns([2.2, 1.8])
    
    if not df_f.empty:
        monthly = df_f.groupby('Bulan')[rev_col].sum().reindex(range(1,13), fill_value=0)
        fig_m = px.bar(x=[bulan_dict[i] for i in monthly.index], y=monthly.values, color_discrete_sequence=['#ffa726'])
        fig_m.update_layout(height=280, margin=dict(l=20,r=20,t=20,b=20), xaxis_title="", yaxis_title="")
        c_graf1.subheader("📅 Bulanan")
        c_graf1.plotly_chart(fig_m, use_container_width=True)

        jp = df_f.groupby(jenis_col)[rev_col].sum()
        fig_jp = px.pie(names=jp.index, values=jp.values, hole=0.5, color_discrete_sequence=['#ffa726', '#8d6e63', '#d7ccc8'])
        fig_jp.update_layout(height=280, margin=dict(l=20,r=20,t=20,b=20))
        c_graf2.subheader("🛒 Jenis Penjualannya")
        c_graf2.plotly_chart(fig_jp, use_container_width=True)

    c_r2_1, c_r2_2, c_r2_3 = st.columns([1.5, 1.8, 1.7])
    
    if not df_f.empty:
        yt = df_f.groupby('Tahun')[rev_col].sum()
        fig_yt = px.bar(x=yt.values/1e6, y=[str(t) for t in yt.index], orientation='h', color_discrete_sequence=['#ffa726'])
        fig_yt.update_layout(height=240, margin=dict(l=20,r=20,t=20,b=20), xaxis_title="Jt", yaxis_title="")
        c_r2_1.subheader("💲 Penjualan/Tahun")
        c_r2_1.plotly_chart(fig_yt, use_container_width=True)

        cat_s = df_f.groupby(cat_col)[rev_col].sum()
        fig_cat = px.bar(x=cat_s.index, y=cat_s.values, color_discrete_sequence=['#8d6e63'])
        fig_cat.update_layout(height=240, margin=dict(l=20,r=20,t=20,b=20), xaxis_title="", yaxis_title="")
        c_r2_2.subheader("📦 Penjualan/Kategori")
        c_r2_2.plotly_chart(fig_cat, use_container_width=True)

        pay_s = df_f.groupby(pay_col)[rev_col].sum()
        fig_pay = px.pie(names=pay_s.index, values=pay_s.values, hole=0.5, color_discrete_sequence=['#ffa726', '#8d6e63'])
        fig_pay.update_layout(height=240, margin=dict(l=20,r=20,t=20,b=20))
        c_r2_3.subheader("💳 Cara Pembayaran")
        c_r2_3.plotly_chart(fig_pay, use_container_width=True)

with col_right_panel:
    st.subheader("📦 10 Produk Terlaris")
    if not df_f.empty:
        top10 = df_f.groupby(prod_col)[qty_col].sum().nlargest(10)
        df_top10 = pd.DataFrame({'Produk': top10.index, 'Qty': top10.values}).sort_values(by='Qty', ascending=True)
        fig_top10 = px.bar(df_top10, x='Qty', y='Produk', orientation='h', color_discrete_sequence=['#ffa726'])
        fig_top10.update_layout(height=580, margin=dict(l=10,r=10,t=20,b=20), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_top10, use_container_width=True)

with st.expander(f"📄 Lihat Data Transaksi Lengkap (Total: {len(df_f)} baris dari {len(df)} total data)"):
    st.dataframe(df_f, use_container_width=True)
