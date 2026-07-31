"""
Dashboard Indepth Stunting - Kelurahan Satimpo
===============================================
Format data: Google Forms CSV (separator ;, multi-select dalam 1 kolom)
streamlit run dashboard_stunting_satimpo.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import gc, re
import plotly.io as pio

# ===== KONFIGURASI FONT =====
FONT_SIZE = 16
FONT_SIZE_TITLE = 19
FONT_SIZE_SUBTITLE = 17
FONT_SIZE_TRACE = 15
FONT_SIZE_LEGEND = 14

pio.templates['custom'] = pio.templates['plotly']
pio.templates['custom'].layout.font = dict(color='#1E293B', size=FONT_SIZE)
pio.templates['custom'].layout.title = dict(font=dict(size=FONT_SIZE_TITLE))
pio.templates.default = 'custom'

st.set_page_config(page_title="Indepth Stunting - Satimpo",page_icon="📋",layout="wide",initial_sidebar_state="expanded")

# CSS untuk styling dashboard dan menu
st.markdown("""
<style>
.main .block-container{padding:1rem 2rem;max-width:1400px}
.dh{background:linear-gradient(135deg,#0F766E,#115E59 50%,#134E4A);padding:1.5rem 2rem;border-radius:14px;color:#fff;margin-bottom:1.5rem;box-shadow:0 4px 20px rgba(15,118,110,.3)}
.dh h1{margin:0;font-size:1.7rem;font-weight:700} .dh p{margin:.4rem 0 0;opacity:.9;font-size:.95rem}
.sh{font-size:1.15rem;font-weight:700;color:#134E4A;margin:1.5rem 0 .8rem;padding-bottom:.4rem;border-bottom:3px solid #0F766E}
.card{background:#F0FDFA;border:1px solid #99F6E4;border-radius:10px;padding:1rem 1.2rem;margin:.5rem 0}
[data-testid="stMetric"]{background:linear-gradient(135deg,#FFF,#F0FDFA);border:1px solid #CCFBF1;border-radius:10px;padding:.8rem;box-shadow:0 2px 6px rgba(0,0,0,.04)}
[data-testid="stMetricLabel"]{font-weight:600!important;color:#475569!important}
[data-testid="stMetricValue"]{font-size:1.4rem!important;font-weight:700!important;color:#134E4A!important}
#MainMenu{visibility:hidden}footer{visibility:hidden}

/* ===== CSS UNTUK MENU BUTTON ===== */
div[data-testid="column"] {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.menu-btn {
    width: 100%;
    padding: 16px 8px;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    background: #F8FAFC;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    text-align: center;
    font-family: inherit;
    position: relative;
    overflow: hidden;
}

.menu-btn:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    border-color: #0F766E;
    background: #F0FDFA;
}

.menu-btn.active {
    background: linear-gradient(135deg, #0F766E, #115E59);
    border-color: #0F766E;
    box-shadow: 0 4px 15px rgba(15,118,110,0.4);
    transform: translateY(-2px);
}

.menu-btn.active .menu-icon {
    filter: brightness(0) invert(1);
}

.menu-btn.active .menu-label {
    color: white !important;
}

.menu-btn .menu-icon {
    font-size: 28px;
    display: block;
    margin-bottom: 4px;
    transition: all 0.3s ease;
}

.menu-btn .menu-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #1E293B;
    transition: all 0.3s ease;
}

.menu-btn .menu-badge {
    position: absolute;
    top: -8px;
    right: -8px;
    background: #DC2626;
    color: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    font-size: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(220,38,38,0.3);
}

/* Sembunyikan label button default Streamlit */
.stButton button {
    width: 100%;
    height: auto !important;
    min-height: 80px;
    padding: 12px 8px !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    font-family: inherit !important;
    font-size: inherit !important;
    line-height: 1.2 !important;
    white-space: normal !important;
    word-wrap: break-word !important;
}

.stButton button:hover {
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
    transform: none !important;
}

.stButton button:focus {
    box-shadow: none !important;
}

.stButton button:active {
    box-shadow: none !important;
    transform: none !important;
}

/* Responsif untuk mobile */
@media (max-width: 768px) {
    .menu-btn .menu-icon {
        font-size: 22px;
    }
    .menu-btn .menu-label {
        font-size: 0.75rem;
    }
    .stButton button {
        min-height: 60px;
        padding: 8px 4px !important;
    }
}
</style>
""",unsafe_allow_html=True)

# ===== UTILITAS =====
def pct(n,t): return round((n/t)*100,1) if t>0 else 0
def fmt(x): return f"{x:.1f}".replace(".",",")+"%"

def col_find(df, keyword):
    """Find column by keyword (case-insensitive partial match)"""
    for c in df.columns:
        if keyword.lower() in c.lower(): return c
    return None

def multi_count(series, pattern):
    """Count rows where multi-select column contains pattern"""
    return series.astype(str).str.contains(pattern, case=False, na=False).sum()

def bar_multi(df, col, items, labels, title, clr="#0D9488"):
    """Bar chart from multi-select column"""
    n = len(df)
    if col not in df.columns: return None
    rows = [{"Variabel": lbl, "Jumlah": multi_count(df[col], pat), "Persen": pct(multi_count(df[col], pat), n)}
            for pat, lbl in zip(items, labels)]
    p = pd.DataFrame(rows)
    fig = px.bar(p, x="Persen", y="Variabel", orientation="h", title=title,
                 text=p["Persen"].apply(fmt), color_discrete_sequence=[clr])
    fig.update_traces(textposition="outside", cliponaxis=False, textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
    fig.update_layout(
        font=dict(size=FONT_SIZE, color='#1E293B'),
        title=dict(font=dict(size=FONT_SIZE_TITLE)),
        height=max(300, len(rows)*55),
        xaxis=dict(range=[0,110], tickfont=dict(size=FONT_SIZE), title_font=dict(size=FONT_SIZE_SUBTITLE)),
        yaxis=dict(tickfont=dict(size=FONT_SIZE)),
        margin=dict(l=10,r=60,t=70,b=30),
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def bar_yn(df, col, title, clr="#0D9488"):
    """Simple Ya/Tidak bar"""
    if col not in df.columns: return None
    n = len(df)
    ya = (df[col].astype(str).str.strip().str.lower() == "ya").sum()
    return ya, n

def dist_bar(series, bins, labels, title, clr, threshold_index=None, threshold_label=None):
    """Create distribution bar chart with optional threshold line at specific index"""
    s = pd.to_numeric(series.astype(str).str.replace(",","."), errors='coerce').dropna()
    cat = pd.cut(s, bins=bins, labels=labels, right=False)
    dist = cat.value_counts().sort_index().reset_index(); dist.columns = ['Interval','Jumlah']
    modus = dist.loc[dist['Jumlah'].idxmax()]
    fig = px.bar(dist, x='Interval', y='Jumlah', text='Jumlah', title=title, color_discrete_sequence=[clr])
    fig.update_traces(textposition='outside',cliponaxis=False,textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
    
    # Tambahkan garis threshold jika ada
    if threshold_index is not None and threshold_label is not None:
        # threshold_index adalah posisi bar dimana garis akan diletakkan
        # Garis diletakkan di antara bar threshold_index-1 dan threshold_index
        x_pos = threshold_index - 0.5
        fig.add_shape(type="line", 
                     x0=x_pos, 
                     x1=x_pos, 
                     y0=0, 
                     y1=1, 
                     yref="paper",
                     line=dict(color="red", width=2.5, dash="dash"))
        fig.add_annotation(x=x_pos, 
                          y=1, 
                          yref="paper", 
                          text=threshold_label,
                          showarrow=False,
                          font=dict(color="red", size=FONT_SIZE-1, weight="bold"),
                          xanchor="right",
                          yanchor="bottom",
                          xshift=-4)
    
    fig.update_layout(
        font=dict(size=FONT_SIZE, color='#1E293B'),
        title=dict(font=dict(size=FONT_SIZE_TITLE)),
        height=400,
        xaxis=dict(tickfont=dict(size=FONT_SIZE)),
        yaxis=dict(tickfont=dict(size=FONT_SIZE)),
        margin=dict(l=10,r=10,t=70,b=30), 
        showlegend=False
    )
    return fig, modus['Interval'], int(modus['Jumlah']), s

def to_num(series):
    return pd.to_numeric(series.astype(str).str.replace(",","."), errors='coerce')

# ===== COLUMN NAME MAPPING (partial match) =====
C = {
    'morb': 'didiagnosis keluhan',
    'kehamilan_ke': 'adalah yang ke',
    'jarak': 'Jarak kehamilan',
    'alergi': 'alergi berikut',
    'bb_balita': 'Berat Badan  [NAMA BALITA]',
    'akses': 'mengakses layanan kesehatan',
    'umur_ibu': 'Umur ibu pada saat',
    'tinggi_ayah': 'Tinggi [AYAH',
    'berat_ayah': 'Berat Badan [AYAH',
    'tinggi_ibu': 'Tinggi [IBU',
    'berat_ibu': 'Berat Badan [IBU',
    'anc': 'pemeriksaan kehamilan (ANC)',
    'tempat_anc': 'Tempat pemeriksaan',
    'ttd': 'TTD',
    'mms': 'MMS',
    'komplikasi': 'komplikasi kehamilan',
    'ibu_hamil': 'sedang hamil',
    'pengasuh': 'mengasuh/mengurus',
    'ditinggalkan': 'ditinggalkan oleh pengasuh',
    'dititipkan': 'dititipkan atau diasuh',
    'sendiri': 'ditinggalkan sendirian',
    'imd': 'IMD',
    'pernah_asi': 'PERNAH disusui',
    'disapih': 'disapih',
    'asi_24jam': 'diberi minuman (cairan) dan atau makanan',
    'umur_mpasi': 'mulai rutin setiap hari',
    'jenis_mpasi': 'jenis minuman (cairan)/makanan selain ASI',
    'kons_balita': 'makanan apa sajakah yang dimakan  [NAMA BALITA]',
    'kons_ibu': 'makanan apa sajakah yang dimakan  [IBU',
    'frek_lengkap': 'makan makanan lengkap',
    'frek_kudapan': 'makan makanan kudapan',
    'kia': 'buku KIA',
    'usia_kehamilan': 'Usia kehamilan saat',
    'bb_lahir': 'Berat bayi lahir',
    'pb_lahir': 'Panjang bayi lahir',
    'tgl_lahir': 'Tanggal Lahir [BALITA]',
    'posyandu': 'Posyandu',
}

def g(df, key):
    """Get column by key from mapping"""
    return col_find(df, C.get(key, key))

# ===== LOAD =====
@st.cache_data(ttl=3600, max_entries=1)
def load_data():
    for enc in ['utf-8','cp1252','latin1']:
        try: return pd.read_csv("DATA_STUNTING_SAMPLE_48.csv", sep=';', encoding=enc)
        except: continue
    return pd.read_csv("DATA_STUNTING_SAMPLE_48.csv", sep=';', encoding='utf-8', errors='replace')

# ===== 1. RINGKASAN =====
def page_ringkasan(df):
    n = len(df)
    tgl_col = g(df,'tgl_lahir')
    umur_bulan = None
    if tgl_col:
        tgl_lahir = pd.to_datetime(df[tgl_col], format='mixed', dayfirst=False, errors='coerce')
        timestamp = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=False, errors='coerce')
        umur_bulan = ((timestamp - tgl_lahir).dt.days / 30.44).round(0)

    # Posisi Satimpo
    st.markdown('<div class="sh">📍 Posisi Satimpo di Kota Bontang</div>',unsafe_allow_html=True)
    kel=pd.DataFrame({'Kelurahan':['TANJUNG LAUT INDAH','BONTANG LESTARI','BEREBAS PANTAI','Tanjung Laut',
        'BEREBAS TENGAH','LOK TUAN','GUNTUNG','SATIMPO','API-API','BONTANG KUALA',
        'BELIMBING','GUNUNG TELIHAN','BONTANG BARU','GUNUNG ELAI','KANAAN'],
        'Prevalensi':[19.44,19.35,18.09,17.90,17.65,17.59,15.10,13.83,11.85,11.57,11.16,9.69,8.56,7.99,7.84]
    }).sort_values('Prevalensi',ascending=True)
    c1,c2=st.columns([2,1])
    with c1:
        colors=['#DC2626' if k=='SATIMPO' else '#94A3B8' for k in kel['Kelurahan']]
        fig=px.bar(kel,x='Prevalensi',y='Kelurahan',orientation='h',text=kel['Prevalensi'].apply(lambda x:f'{x:.2f}%'.replace('.',',')),
                   title='📊 Prevalensi Stunting per Kelurahan — Juni 2026')
        fig.update_traces(marker_color=colors,textposition='outside',cliponaxis=False,textfont=dict(size=FONT_SIZE_TRACE))
        fig.add_vline(x=14.05,line_dash='dash',line_color='#0F766E',annotation_text='Kota Bontang: 14,05%',annotation_font_color='#1E293B',annotation_position='bottom right')
        fig.update_layout(
            font=dict(size=FONT_SIZE, color='#1E293B'),
            title=dict(font=dict(size=FONT_SIZE_TITLE)),
            height=550,
            xaxis=dict(range=[0,25], tickfont=dict(size=FONT_SIZE), title_font=dict(size=FONT_SIZE_SUBTITLE)),
            yaxis=dict(tickfont=dict(size=FONT_SIZE)),
            margin=dict(l=10,r=80,t=70,b=30)
        )
        st.plotly_chart(fig,use_container_width=True); del fig
    with c2:
        st.markdown("""<div class="card"><div style="font-size:1rem;font-weight:600;color:#134E4A;margin-bottom:.8rem">📋 Satimpo</div>
        <table style="width:100%;font-size:.95rem;line-height:2.2"><tr><td>Balita ditimbang</td><td style="text-align:right"><b>347</b></td></tr>
        <tr><td>Balita stunting</td><td style="text-align:right"><b>48</b></td></tr><tr><td>Prevalensi</td><td style="text-align:right"><b>13,83%</b></td></tr>
        <tr style="border-top:1px solid #99F6E4"><td>Peringkat</td><td style="text-align:right"><b>8 dari 15</b></td></tr></table></div>
        <div class="card" style="margin-top:.8rem"><div style="font-size:.9rem;color:#475569;line-height:1.6">
        <b>Catatan:</b> Grafik = prevalensi seluruh balita (data rutin). Dashboard = profil 48 balita stunting.</div></div>""",unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<div class="sh">📊 Ringkasan Responden</div>',unsafe_allow_html=True)
    kia_col=g(df,'kia'); kia_ya=(df[kia_col].astype(str).str.lower()=='ya').sum() if kia_col else 0
    c1,c2=st.columns(2)
    with c1: st.metric("👶 Total Balita Stunting",f"{n} balita"); st.markdown('<p style="color:#0F766E;font-size:.9rem;margin-top:-10px">Dari 347 balita ditimbang (13,83%)</p>',unsafe_allow_html=True)
    with c2: st.metric("📖 Punya Buku KIA",f"{kia_ya} dari {n}"); st.markdown(f'<p style="color:#0F766E;font-size:.9rem;margin-top:-10px">{fmt(pct(kia_ya,n))}</p>',unsafe_allow_html=True)

    # Distribusi
    st.markdown('<div class="sh">📊 Distribusi Karakteristik</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        if umur_bulan is not None:
            fig,m,mn,_=dist_bar(umur_bulan,[0,6,12,24,36,48,60],['0-5 bln','6-11 bln','12-23 bln','24-35 bln','36-47 bln','48-59 bln'],'📊 Umur Balita','#0D9488')
            st.plotly_chart(fig,use_container_width=True); del fig
            st.markdown(f'<div class="card">👶 Terbanyak: <b>{m}</b> ({mn} balita)</div>',unsafe_allow_html=True)
    with c2:
        col=g(df,'bb_balita')
        if col:
            fig,m,mn,_=dist_bar(df[col],[0,6,8,10,12,14,16,20],['< 6','6-7,9','8-9,9','10-11,9','12-13,9','14-15,9','≥ 16'],'📊 Berat Badan Balita (kg)','#2563EB')
            st.plotly_chart(fig,use_container_width=True); del fig
            st.markdown(f'<div class="card">⚖️ Terbanyak: <b>{m} kg</b> ({mn} balita)</div>',unsafe_allow_html=True)

    c3,c4=st.columns(2)
    with c3:
        col=g(df,'umur_ibu')
        if col:
            fig,m,mn,_=dist_bar(df[col],[15,20,25,30,35,40,50],['15-19','20-24','25-29','30-34','35-39','≥ 40'],'📊 Umur Ibu saat Hamil','#7C3AED')
            st.plotly_chart(fig,use_container_width=True); del fig
            st.markdown(f'<div class="card">👩 Terbanyak: <b>{m} tahun</b> ({mn} ibu)</div>',unsafe_allow_html=True)
    with c4:
        col=g(df,'bb_balita')  # placeholder empty
        pass

    # Alergi
    col=g(df,'alergi')
    if col:
        st.markdown('<div class="sh">🤧 Alergi Balita</div>',unsafe_allow_html=True)
        fig=bar_multi(df,col,['Susu Sapi','Seafood','Telur','Kacang'],['Susu Sapi','Seafood','Telur','Kacang-kacangan'],'📊 Prevalensi Alergi','#F59E0B')
        if fig: st.plotly_chart(fig,use_container_width=True); del fig

    # Morbiditas
    col=g(df,'morb')
    if col:
        st.markdown('<div class="sh">🏥 Morbiditas Balita</div>',unsafe_allow_html=True)
        fig=bar_multi(df,col,['Infeksi Saluran Pernapasan Akut','DIARE','PNEUMONIA','Tuberkulosis'],['Infeksi Saluran Pernapasan Akut','Diare','Pneumonia','Tuberkulosis Paru'],'📊 Prevalensi Penyakit','#DC2626')
        if fig: st.plotly_chart(fig,use_container_width=True); del fig

    # Kelahiran
    st.markdown('<div class="sh">👶 Karakteristik Kelahiran</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    
    # BB Lahir - threshold di index 1 (antara '< 2500' dan '2500-2999')
    col=g(df,'bb_lahir')
    if col:
        with c1:
            fig,m,mn,s=dist_bar(df[col],[0,2500,3000,3500,4000,5000],
                               ['< 2500','2500-2999','3000-3499','3500-3999','≥ 4000'],
                               '📊 BB Lahir (gram)','#0D9488',1,'< 2500 g (BBLR)')
            st.plotly_chart(fig,use_container_width=True); del fig
            cnt=(s<2500).sum()
            st.markdown(f'<div class="card">Terbanyak: <b>{m}</b> ({mn}) | ⚠️ BBLR: <b>{cnt}</b> ({fmt(pct(cnt,len(s)))})</div>',unsafe_allow_html=True)
    
    # PB Lahir - threshold di index 1 (antara '< 48' dan '48-49')
    col=g(df,'pb_lahir')
    if col:
        with c2:
            fig,m,mn,s=dist_bar(df[col],[0,48,50,52,55],
                               ['< 48','48-49','50-51','≥ 52'],
                               '📊 PB Lahir (cm)','#2563EB',1,'< 48 cm (Pendek)')
            st.plotly_chart(fig,use_container_width=True); del fig
            cnt=(s<48).sum()
            st.markdown(f'<div class="card">Terbanyak: <b>{m}</b> ({mn}) | ⚠️ Pendek: <b>{cnt}</b> ({fmt(pct(cnt,len(s)))})</div>',unsafe_allow_html=True)
    
    # Usia Kehamilan - threshold di index 1 (antara '< 37' dan '37-38')
    col=g(df,'usia_kehamilan')
    if col:
        with c3:
            fig,m,mn,s=dist_bar(df[col],[0,37,39,41,45],
                               ['< 37','37-38','39-40','≥ 41'],
                               '📊 Usia Kehamilan (mg)','#7C3AED',1,'< 37 mg (Prematur)')
            st.plotly_chart(fig,use_container_width=True); del fig
            cnt=(s<37).sum()
            st.markdown(f'<div class="card">Terbanyak: <b>{m}</b> ({mn}) | ⚠️ Prematur: <b>{cnt}</b> ({fmt(pct(cnt,len(s)))})</div>',unsafe_allow_html=True)

    gc.collect()

# ===== 2. RIWAYAT KEHAMILAN =====
def page_kehamilan(df):
    n=len(df)
    st.markdown('<div class="sh">🤰 Kondisi Ibu saat Kehamilan Balita</div>',unsafe_allow_html=True)

    c1,c2=st.columns(2)
    with c1:
        col=g(df,'umur_ibu')
        if col:
            fig,m,mn,_=dist_bar(df[col],[15,20,25,30,35,40,50],['15-19','20-24','25-29','30-34','35-39','≥ 40'],'📊 Umur Ibu saat Hamil (tahun)','#7C3AED')
            st.plotly_chart(fig,use_container_width=True); del fig
            st.markdown(f'<div class="card">👩 Terbanyak: <b>{m} tahun</b> ({mn} ibu)</div>',unsafe_allow_html=True)
    with c2:
        col=g(df,'berat_ibu')
        if col:
            fig,m,mn,_=dist_bar(df[col],[30,40,45,50,55,60,65,70,100],['< 40','40-44','45-49','50-54','55-59','60-64','65-69','≥ 70'],'📊 Berat Badan Ibu (kg)','#EC4899')
            st.plotly_chart(fig,use_container_width=True); del fig
            st.markdown(f'<div class="card">⚖️ Terbanyak: <b>{m} kg</b> ({mn} ibu)</div>',unsafe_allow_html=True)

    st.markdown('<div class="sh">📏 Tinggi Badan Orang Tua</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        col=g(df,'tinggi_ayah')
        if col:
            # Threshold di index 1 (antara '< 160' dan '160-164')
            fig,m,mn,s=dist_bar(df[col],[0,160,165,170,175,190],
                               ['< 160','160-164','165-169','170-174','≥ 175'],
                               '📊 Tinggi Badan Ayah (cm)','#0891B2',1,'< 160 cm')
            st.plotly_chart(fig,use_container_width=True); del fig
            pdk=(s<160).sum()
            st.markdown(f'<div class="card">📏 Terbanyak: <b>{m}</b> ({mn}) | Pendek (< 160 cm): <b>{pdk}</b> ({fmt(pct(pdk,len(s)))})</div>',unsafe_allow_html=True)
    with c2:
        col=g(df,'tinggi_ibu')
        if col:
            # Threshold di index 1 (antara '< 150' dan '150-154')
            fig,m,mn,s=dist_bar(df[col],[0,150,155,160,165,175],
                               ['< 150','150-154','155-159','160-164','≥ 165'],
                               '📊 Tinggi Badan Ibu (cm)','#D946EF',1,'< 150 cm')
            st.plotly_chart(fig,use_container_width=True); del fig
            pdk=(s<150).sum()
            st.markdown(f'<div class="card">📏 Terbanyak: <b>{m}</b> ({mn}) | Pendek (< 150 cm): <b>{pdk}</b> ({fmt(pct(pdk,len(s)))})</div>',unsafe_allow_html=True)

    st.markdown('<div class="sh">📊 Paritas dan Jarak Kehamilan</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    col=g(df,'kehamilan_ke')
    if col:
        par=to_num(df[col]).dropna()
        pd_dist=par.value_counts().sort_index().reset_index(); pd_dist.columns=['Ke-','Jumlah']
        mp=pd_dist.loc[pd_dist['Jumlah'].idxmax()]
        with c1:
            fig=px.bar(pd_dist,x='Ke-',y='Jumlah',text='Jumlah',title='📊 Distribusi Paritas (Kehamilan ke-)',color_discrete_sequence=['#6366F1'])
            fig.update_traces(textposition='outside',cliponaxis=False,textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
            # Tambahkan garis threshold untuk grande multipara (>=4)
            fig.add_shape(type="line", x0=3.5, x1=3.5, y0=0, y1=1, yref="paper",
                         line=dict(color="red", width=2.5, dash="dash"))
            fig.add_annotation(x=3.5, y=1, yref="paper", text="≥ 4 (Grande Multipara)",
                              showarrow=False, font=dict(color="red", size=FONT_SIZE-1, weight="bold"),
                              xanchor="right", yanchor="bottom", xshift=-4)
            fig.update_layout(
                font=dict(size=FONT_SIZE, color='#1E293B'),
                title=dict(font=dict(size=FONT_SIZE_TITLE)),
                height=400,
                xaxis=dict(tickfont=dict(size=FONT_SIZE)),
                yaxis=dict(tickfont=dict(size=FONT_SIZE)),
                margin=dict(l=10,r=10,t=70,b=30)
            )
            st.plotly_chart(fig,use_container_width=True); del fig
            gm=(par>=4).sum()
            st.markdown(f'<div class="card">Terbanyak: ke-<b>{int(mp["Ke-"])}</b> ({int(mp["Jumlah"])}) | ⚠️ Grande multipara (≥ 4): <b>{gm}</b> ({fmt(pct(gm,len(par)))})</div>',unsafe_allow_html=True)
    col_j=g(df,'jarak')
    if col_j:
        with c2:
            j=df[col_j].value_counts().reset_index(); j.columns=['Jarak','Jumlah']
            fig=px.pie(j,names='Jarak',values='Jumlah',title='📊 Jarak Kehamilan',hole=.4,color_discrete_sequence=['#10B981','#F87171'])
            fig.update_traces(textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
            fig.update_layout(
                font=dict(size=FONT_SIZE, color='#1E293B'),
                title=dict(font=dict(size=FONT_SIZE_TITLE)),
                height=400,
                margin=dict(l=10,r=10,t=70,b=10)
            )
            st.plotly_chart(fig,use_container_width=True); del fig

    st.markdown('<div class="sh">🏥 Pemeriksaan Kehamilan</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        col_anc=g(df,'anc')
        if col_anc:
            fig=bar_multi(df,col_anc,['Dokter kandungan','Dokter umum','Bidan','Tenaga kesehatan lainnya'],
                          ['Dokter Kandungan','Dokter Umum','Bidan','Tenaga Kesehatan Lainnya'],'📊 Tenaga Pemeriksa Kehamilan','#6366F1')
            if fig: st.plotly_chart(fig,use_container_width=True); del fig
    with c2:
        col_tempat=g(df,'tempat_anc')
        if col_tempat:
            t=df[col_tempat].value_counts().reset_index(); t.columns=['Tempat','Jumlah']
            fig=px.pie(t,names='Tempat',values='Jumlah',title='📊 Tempat Pemeriksaan Kehamilan',hole=.4,color_discrete_sequence=px.colors.qualitative.Safe)
            fig.update_traces(textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
            fig.update_layout(
                font=dict(size=FONT_SIZE, color='#1E293B'),
                title=dict(font=dict(size=FONT_SIZE_TITLE)),
                height=400,
                margin=dict(l=10,r=10,t=70,b=10)
            )
            st.plotly_chart(fig,use_container_width=True); del fig

    st.markdown('<div class="sh">💊 Suplementasi saat Hamil</div>',unsafe_allow_html=True)
    items=[('ttd','Mendapat Tablet Tambah Darah (TTD)'),('mms','Mendapat Suplemen Multi Vitamin Mineral (MMS)')]
    rows=[]
    for key,lbl in items:
        col=g(df,key)
        if col:
            ya=(df[col].astype(str).str.lower()=='ya').sum()
            rows.append({"Variabel":lbl,"Jumlah":ya,"Persen":pct(ya,n)})
    if rows:
        p=pd.DataFrame(rows)
        fig=px.bar(p,x='Persen',y='Variabel',orientation='h',text=p['Persen'].apply(fmt),color_discrete_sequence=['#8B5CF6'])
        fig.update_traces(textposition='outside',cliponaxis=False,textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
        fig.update_layout(
            font=dict(size=FONT_SIZE, color='#1E293B'),
            title=dict(font=dict(size=FONT_SIZE_TITLE)),
            height=250,
            xaxis=dict(range=[0,110], tickfont=dict(size=FONT_SIZE), title_font=dict(size=FONT_SIZE_SUBTITLE)),
            yaxis=dict(tickfont=dict(size=FONT_SIZE)),
            margin=dict(l=10,r=60,t=70,b=30)
        )
        st.plotly_chart(fig,use_container_width=True); del fig

    col=g(df,'komplikasi')
    if col:
        st.markdown('<div class="sh">⚠️ Komplikasi Kehamilan</div>',unsafe_allow_html=True)
        pats=['Hipertensi','Pre-eklampsia','Anemia','KEK','Obesitas','Diabetes','Jantung','Perdarahan','Infeksi','janin terhambat']
        lbls=['Hipertensi','Pre-eklampsia','Anemia (Hb < 11 g/dl)','Kurang Energi Kronis (Lingkar Lengan < 23,5 cm)','Obesitas/Berat Badan Berlebih','Diabetes','Gangguan Jantung','Perdarahan','Infeksi (Malaria, TBC, HIV, Sifilis, Hepatitis B)','Pertumbuhan Janin Terhambat']
        fig=bar_multi(df,col,pats,lbls,'📊 Komplikasi Kehamilan Ibu','#E11D48')
        if fig: st.plotly_chart(fig,use_container_width=True); del fig

    gc.collect()

# ===== 3. IMUNISASI =====
def page_imunisasi(df):
    n=len(df)
    st.markdown('<div class="sh">💉 Cakupan Imunisasi</div>',unsafe_allow_html=True)
    imun_names=['Hepatitis B 0','BCG','DPT-HB-Hib 1','DPT-HB-Hib 2','DPT-HB-Hib 3','DPT-HB-Hib Lanjutan',
                'PCV 1','PCV 2','PCV 3','Campak-Rubella (MR)','Campak-Rubella lanjutan (MR/MMR)',
                'Rotavirus 1','Rotavirus 2','Rotavirus 3','Polio 1','Polio 2','Polio 3','Polio 4',
                'Polio suntik/injeksi Tambahan 1','Polio suntik/injeksi Tambahan 2']
    rows=[]
    for name in imun_names:
        if name in df.columns:
            ya=(df[name].astype(str).str.lower()=='ya').sum()
            rows.append({'Imunisasi':name,'Sudah':ya,'Belum':n-ya,'Cakupan':pct(ya,n)})
    if rows:
        idf=pd.DataFrame(rows).sort_values('Cakupan',ascending=True)
        fig=px.bar(idf,x='Cakupan',y='Imunisasi',orientation='h',text=idf['Cakupan'].apply(fmt),color='Cakupan',color_continuous_scale=['#DC2626','#F59E0B','#16A34A'],color_continuous_midpoint=50)
        fig.update_traces(textposition='outside',cliponaxis=False,textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
        fig.add_vline(x=80,line_dash='dash',line_color='red',annotation_text='Target 80%',annotation_font_color='red')
        fig.update_layout(
            font=dict(size=FONT_SIZE, color='#1E293B'),
            title=dict(font=dict(size=FONT_SIZE_TITLE)),
            height=max(550,len(rows)*35),
            xaxis=dict(range=[0,110], tickfont=dict(size=FONT_SIZE), title_font=dict(size=FONT_SIZE_SUBTITLE)),
            yaxis=dict(tickfont=dict(size=FONT_SIZE-1)),
            margin=dict(l=10,r=60,t=70,b=30),
            showlegend=False
        )
        st.plotly_chart(fig,use_container_width=True); del fig

        st.markdown('<div class="sh">🎯 Imunisasi Dasar Lengkap</div>',unsafe_allow_html=True)
        idl=[c for c in ['Hepatitis B 0','BCG','DPT-HB-Hib 1','DPT-HB-Hib 2','DPT-HB-Hib 3','Polio 1','Polio 2','Polio 3','Polio 4','Campak-Rubella (MR)'] if c in df.columns]
        chk=df[idl].apply(lambda s:s.astype(str).str.lower()=='ya')
        lgk=chk.all(axis=1).sum()
        c1,c2=st.columns([1,2])
        with c1:
            fig=go.Figure(go.Pie(labels=['Lengkap','Tidak'],values=[lgk,n-lgk],marker_colors=['#10B981','#F87171'],hole=.5,textinfo='value+percent',textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B')))
            fig.update_layout(
                font=dict(size=FONT_SIZE, color='#1E293B'),
                title=dict(font=dict(size=FONT_SIZE_TITLE)),
                height=320,
                margin=dict(l=10,r=10,t=20,b=10)
            )
            st.plotly_chart(fig,use_container_width=True); del fig
        with c2:
            st.markdown(f'<div class="card" style="font-size:1rem"><b>IDL</b> = 10 imunisasi wajib<br><br>✅ Lengkap: <b>{lgk} ({fmt(pct(lgk,n))})</b><br>❌ Tidak: <b>{n-lgk} ({fmt(pct(n-lgk,n))})</b></div>',unsafe_allow_html=True)
    gc.collect()

# ===== 4. ASI & MPASI =====
def page_asi_mpasi(df):
    n=len(df)
    st.markdown('<div class="sh">🍼 Praktik Pemberian Air Susu Ibu</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        items=[('imd','Inisiasi Menyusui Dini'),('pernah_asi','Pernah Diberi ASI')]
        rows=[]
        for key,lbl in items:
            col=g(df,key)
            if col:
                ya=(df[col].astype(str).str.lower()=='ya').sum()
                rows.append({"Variabel":lbl,"Persen":pct(ya,n)})
        if rows:
            p=pd.DataFrame(rows)
            fig=px.bar(p,x='Persen',y='Variabel',orientation='h',text=p['Persen'].apply(fmt),color_discrete_sequence=['#0D9488'])
            fig.update_traces(textposition='outside',cliponaxis=False,textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
            fig.update_layout(
                font=dict(size=FONT_SIZE, color='#1E293B'),
                title=dict(font=dict(size=FONT_SIZE_TITLE)),
                height=250,
                xaxis=dict(range=[0,110], tickfont=dict(size=FONT_SIZE), title_font=dict(size=FONT_SIZE_SUBTITLE)),
                yaxis=dict(tickfont=dict(size=FONT_SIZE)),
                margin=dict(l=10,r=60,t=70,b=30)
            )
            st.plotly_chart(fig,use_container_width=True); del fig

    with c2:
        col=g(df,'disapih')
        if col:
            sapih=to_num(df[col]).dropna()
            if len(sapih)>0:
                # Threshold di index 4 (antara '18-23' dan '≥ 24')
                fig,m,mn,_=dist_bar(sapih,[0,6,12,18,24,30],
                                   ['0-5','6-11','12-17','18-23','≥ 24'],
                                   '📊 Umur Berhenti Diberi ASI (bulan)','#F59E0B',4,'< 24 bulan (ASI Dini)')
                st.plotly_chart(fig,use_container_width=True); del fig
                dini=(sapih<24).sum()
                st.markdown(f'<div class="card">⚠️ Berhenti ASI dini (< 24 bulan): <b>{dini}</b> ({fmt(pct(dini,len(sapih)))})</div>',unsafe_allow_html=True)

    col=g(df,'umur_mpasi')
    if col:
        st.markdown('<div class="sh">🥣 Umur Mulai Makanan Pendamping ASI</div>',unsafe_allow_html=True)
        order=["0 - 7 hari","8 - 29 hari","1 - < 2 bulan","2 - < 3 bulan","3 - < 4 bulan","4 - < 5 bulan","5 - < 6 bulan","6 - < 7 bulan","≥ 7 bulan"]
        md=df[col].value_counts().reindex(order).fillna(0).astype(int).reset_index(); md.columns=['Umur','Jumlah']
        fig=px.bar(md,x='Umur',y='Jumlah',text='Jumlah',title='📊 Distribusi Umur Mulai Makanan Pendamping ASI',color_discrete_sequence=['#F59E0B'])
        fig.update_traces(textposition='outside',cliponaxis=False,textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
        # Garis batas: antara "5 - < 6 bulan" (index 6) dan "6 - < 7 bulan" (index 7) → x=6.5
        # Dengan fillna(0), semua 9 kategori selalu ada sehingga posisi index tetap konsisten
        fig.add_shape(type="line", x0=6.5, x1=6.5, y0=0, y1=1, yref="paper",
                     line=dict(color="red", width=2.5, dash="dash"))
        fig.add_annotation(x=6.5, y=1, yref="paper", text="< 6 bulan (Makanan Pendamping Dini)",
                          showarrow=False, font=dict(color="red", size=FONT_SIZE-1, weight="bold"),
                          xanchor="right", yanchor="bottom", xshift=-4)
        fig.update_layout(
            font=dict(size=FONT_SIZE, color='#1E293B'),
            title=dict(font=dict(size=FONT_SIZE_TITLE)),
            height=450,
            xaxis=dict(tickfont=dict(size=FONT_SIZE-1)),
            yaxis=dict(tickfont=dict(size=FONT_SIZE)),
            margin=dict(l=10,r=10,t=70,b=30)
        )
        st.plotly_chart(fig,use_container_width=True); del fig
        dini_l=[l for l in order if l not in ['6 - < 7 bulan','≥ 7 bulan']]
        dc=df[df[col].isin(dini_l)].shape[0]
        st.markdown(f'<div class="card">⚠️ Makanan Pendamping Dini (< 6 bulan): <b>{dc}</b> ({fmt(pct(dc,n))})</div>',unsafe_allow_html=True)

    col=g(df,'jenis_mpasi')
    if col:
        st.markdown('<div class="sh">🥣 Jenis Makanan Pendamping ASI Awal</div>',unsafe_allow_html=True)
        pats=['Susu formula','Susu non-formula','Bubur formula','Biskuit','Bubur tepung','Air tajin','Buah dihaluskan','Bubur nasi','Sari buah','Lainnya']
        fig=bar_multi(df,col,pats,pats,'📊 Jenis Makanan Pendamping ASI Awal','#0891B2')
        if fig: st.plotly_chart(fig,use_container_width=True); del fig

    col=g(df,'kons_balita')
    if col:
        st.markdown('<div class="sh">🍽️ Konsumsi 24 Jam Balita</div>',unsafe_allow_html=True)
        c1,c2=st.columns([2,1])
        pats_b=['padi-padian','Sayuran hijau','Ati, ampela','kacang-kacangan']
        lbls_b=['Serealia/Umbi','Sayur & Buah','Protein Hewani','Kacang/Snack']
        with c1:
            fig=bar_multi(df,col,pats_b,lbls_b,'📊 Kelompok Pangan 24 Jam','#0D9488')
            if fig: st.plotly_chart(fig,use_container_width=True); del fig
        with c2:
            counts=[multi_count(df[col],p) for p in pats_b]
            dds_vals=df[col].apply(lambda x: sum(1 for p in pats_b if p.lower() in str(x).lower()))
            mdd=(dds_vals>=3).sum()
            st.markdown(f"""<div class="card" style="font-size:1rem"><b>📋 Keragaman Pangan (4 kelompok)</b><br><br>
            Memenuhi ≥ 3: <b>{mdd} ({fmt(pct(mdd,n))})</b><br>Tidak: <b>{n-mdd} ({fmt(pct(n-mdd,n))})</b><br><br>
            Rerata: <b>{dds_vals.mean():.1f}</b></div>""",unsafe_allow_html=True)
    gc.collect()

# ===== 5. PENGASUHAN =====
def page_pengasuhan(df):
    n=len(df)
    st.markdown('<div class="sh">🏥 Pengasuhan Balita</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        col=g(df,'pengasuh')
        if col:
            p=df[col].value_counts().reset_index(); p.columns=['Pengasuh','Jumlah']
            fig=px.pie(p,names='Pengasuh',values='Jumlah',title='📊 Pengasuh Utama Sehari-hari',hole=.4,color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
            fig.update_layout(
                font=dict(size=FONT_SIZE, color='#1E293B'),
                title=dict(font=dict(size=FONT_SIZE_TITLE)),
                height=420,
                margin=dict(l=10,r=10,t=70,b=10)
            )
            st.plotly_chart(fig,use_container_width=True); del fig
    with c2:
        col=g(df,'dititipkan')
        if col:
            valid=df[col].dropna().loc[df[col].astype(str).str.strip()!='']
            if len(valid)>0:
                p2=valid.value_counts().reset_index(); p2.columns=['Dititipkan','Jumlah']
                fig=px.pie(p2,names='Dititipkan',values='Jumlah',title='📊 Pengasuh Saat Ditinggal',hole=.4,color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_traces(textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
                fig.update_layout(
                    font=dict(size=FONT_SIZE, color='#1E293B'),
                    title=dict(font=dict(size=FONT_SIZE_TITLE)),
                    height=420,
                    margin=dict(l=10,r=10,t=70,b=10)
                )
                st.plotly_chart(fig,use_container_width=True); del fig

    st.markdown('<div class="sh">📋 Indikator Pola Pengasuhan</div>',unsafe_allow_html=True)
    items=[('akses','Mengakses Layanan Kesehatan'),('ditinggalkan','Pengasuh Meninggalkan Balita untuk Aktivitas Luar'),('sendiri','Balita Ditinggal Sendiri Lebih dari 1 Jam'),('ibu_hamil','Ibu Sedang Hamil Lagi')]
    rows=[]
    for key,lbl in items:
        col=g(df,key)
        if col:
            ya=(df[col].astype(str).str.lower()=='ya').sum()
            rows.append({"Variabel":lbl,"Jumlah":ya,"Persen":pct(ya,n)})
    if rows:
        p=pd.DataFrame(rows)
        fig=px.bar(p,x='Persen',y='Variabel',orientation='h',text=p['Persen'].apply(fmt),color_discrete_sequence=['#0D9488'])
        fig.update_traces(textposition='outside',cliponaxis=False,textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
        fig.update_layout(
            font=dict(size=FONT_SIZE, color='#1E293B'),
            title=dict(font=dict(size=FONT_SIZE_TITLE)),
            height=300,
            xaxis=dict(range=[0,110], tickfont=dict(size=FONT_SIZE), title_font=dict(size=FONT_SIZE_SUBTITLE)),
            yaxis=dict(tickfont=dict(size=FONT_SIZE)),
            margin=dict(l=10,r=60,t=70,b=30)
        )
        st.plotly_chart(fig,use_container_width=True); del fig

    st.markdown("---")
    render_determinan(df)
    gc.collect()

# ===== FUNGSI DETERMINAN =====
def render_determinan(df):
    n=len(df)
    st.markdown('<div class="sh">🔍 Analisis Determinan</div>',unsafe_allow_html=True)
    st.markdown('<div class="card" style="font-size:1rem">Semua responden = anak stunting (total sampling). Fokus: prevalensi faktor risiko untuk intervensi tepat sasaran.</div>',unsafe_allow_html=True)

    rf=[]
    for key,lbl,th,cat in [('bb_lahir','Berat Lahir Rendah (< 2500 gram)',2500,'Kelahiran'),('pb_lahir','Panjang Lahir Pendek (< 48 cm)',48,'Kelahiran'),
                            ('usia_kehamilan','Kelahiran Prematur (< 37 minggu)',37,'Kelahiran'),('tinggi_ibu','Ibu Pendek (Tinggi < 150 cm)',150,'Ibu')]:
        col=g(df,key)
        if col:
            s=to_num(df[col]).dropna(); cnt=(s<th).sum()
            rf.append((lbl,cnt,pct(cnt,n),cat))

    col_k=g(df,'komplikasi')
    if col_k:
        for pat,lbl in [('Anemia','Ibu Anemia saat Hamil'),('KEK','Ibu Kurang Energi Kronis'),('janin terhambat','Pertumbuhan Janin Terhambat')]:
            cnt=multi_count(df[col_k],pat); rf.append((lbl,cnt,pct(cnt,n),'Ibu'))

    col_imd=g(df,'imd')
    if col_imd:
        tdk=(df[col_imd].astype(str).str.lower()!='ya').sum(); rf.append(('Tidak Inisiasi Menyusui Dini',tdk,pct(tdk,n),'Praktik Menyusui'))

    col_m=g(df,'morb')
    if col_m:
        for pat,lbl in [('Infeksi Saluran Pernapasan Akut','Infeksi Saluran Pernapasan Akut'),('DIARE','Diare')]:
            cnt=multi_count(df[col_m],pat); rf.append((lbl,cnt,pct(cnt,n),'Penyakit'))

    col_a=g(df,'akses')
    if col_a:
        tdk=(df[col_a].astype(str).str.lower()!='ya').sum(); rf.append(('Tidak Mengakses Layanan Kesehatan',tdk,pct(tdk,n),'Layanan'))

    col_s=g(df,'sendiri')
    if col_s:
        ya=(df[col_s].astype(str).str.lower()=='ya').sum(); rf.append(('Balita Ditinggal Sendiri > 1 Jam',ya,pct(ya,n),'Pengasuhan'))

    col_mp=g(df,'umur_mpasi')
    if col_mp:
        dini_l=["0 - 7 hari","8 - 29 hari","1 - < 2 bulan","2 - < 3 bulan","3 - < 4 bulan","4 - < 5 bulan","5 - < 6 bulan"]
        dc=df[df[col_mp].isin(dini_l)].shape[0]; rf.append(('Makanan Pendamping Dini',dc,pct(dc,n),'Praktik Menyusui'))

    col_kb=g(df,'kons_balita')
    if col_kb:
        pats_b=['padi-padian','Sayuran hijau','Ati, ampela','kacang-kacangan']
        dds_vals=df[col_kb].apply(lambda x: sum(1 for p in pats_b if p.lower() in str(x).lower()))
        low=(dds_vals<3).sum(); rf.append(('Keragaman Pangan Rendah (< 3 Kelompok)',int(low),pct(low,n),'Pola Makan'))

    if rf:
        rdf=pd.DataFrame(rf,columns=['Faktor Risiko','Jumlah','Prevalensi','Kategori']).sort_values('Prevalensi',ascending=True)
        cat_clr={'Kelahiran':'#2563EB','Ibu':'#DC2626','Penyakit':'#F59E0B','Praktik Menyusui':'#0891B2','Pengasuhan':'#7C3AED','Layanan':'#6366F1','Pola Makan':'#059669'}
        fig=px.bar(rdf,x='Prevalensi',y='Faktor Risiko',orientation='h',text=rdf['Prevalensi'].apply(fmt),color='Kategori',color_discrete_map=cat_clr,title='📊 Prevalensi Faktor Risiko')
        fig.update_traces(textposition='outside',cliponaxis=False,textfont=dict(size=FONT_SIZE_TRACE, color='#1E293B'))
        fig.update_layout(
            font=dict(size=FONT_SIZE, color='#1E293B'),
            title=dict(font=dict(size=FONT_SIZE_TITLE)),
            height=max(550,len(rf)*50),
            xaxis=dict(range=[0,110], tickfont=dict(size=FONT_SIZE), title_font=dict(size=FONT_SIZE_SUBTITLE)),
            yaxis=dict(tickfont=dict(size=FONT_SIZE-1)),
            margin=dict(l=10,r=60,t=70,b=30),
            legend=dict(orientation='h',yanchor='bottom',y=1.02, font=dict(size=FONT_SIZE))
        )
        st.plotly_chart(fig,use_container_width=True); del fig

        st.markdown('<div class="sh">🎯 Top 5 Faktor Risiko</div>',unsafe_allow_html=True)
        for i,(_,row) in enumerate(rdf.nlargest(5,'Prevalensi').iterrows(),1):
            st.markdown(f'<div class="card" style="font-size:1rem"><b>{i}. {row["Faktor Risiko"]}</b> — {row["Jumlah"]} balita ({fmt(row["Prevalensi"])}) [{row["Kategori"]}]</div>',unsafe_allow_html=True)

        st.markdown('<div class="sh">📊 Korelasi Faktor Risiko</div>',unsafe_allow_html=True)
        flags=pd.DataFrame(index=df.index)
        col_bb=g(df,'bb_lahir')
        if col_bb: flags['Berat Lahir Rendah']=to_num(df[col_bb])<2500
        col_ti=g(df,'tinggi_ibu')
        if col_ti: flags['Ibu Pendek']=to_num(df[col_ti])<150
        if col_k:
            flags['Anemia']=df[col_k].astype(str).str.contains('Anemia',case=False,na=False)
            flags['KEK']=df[col_k].astype(str).str.contains('KEK',case=False,na=False)
        if col_imd: flags['Tidak Inisiasi Menyusui Dini']=df[col_imd].astype(str).str.lower()!='ya'
        if col_m:
            flags['Infeksi Saluran Pernapasan Akut']=df[col_m].astype(str).str.contains('Infeksi Saluran Pernapasan Akut',case=False,na=False)
            flags['Diare']=df[col_m].astype(str).str.contains('DIARE',case=False,na=False)
        if len(flags.columns)>=2:
            corr=flags.astype(int).corr().round(2)
            fig=px.imshow(corr,text_auto=True,color_continuous_scale='RdYlGn_r',aspect='auto',labels=dict(color='Korelasi'))
            fig.update_layout(
                font=dict(size=FONT_SIZE, color='#1E293B'),
                title=dict(font=dict(size=FONT_SIZE_TITLE)),
                height=500,
                margin=dict(l=10,r=10,t=70,b=10)
            )
            fig.update_traces(textfont=dict(size=FONT_SIZE_TRACE))
            st.plotly_chart(fig,use_container_width=True); del fig
        del rdf
    gc.collect()

# ===== 6. KONSUMSI IBU =====
def page_konsumsi_ibu(df):
    n=len(df)
    col=g(df,'kons_ibu')
    if col:
        st.markdown('<div class="sh">🍽️ Konsumsi Ibu (24 Jam Terakhir)</div>',unsafe_allow_html=True)
        pats_i=['Air putih','Susu','kaldu','Sayuran hijau','Ati, ampela','kacang-kacangan']
        lbls_i=['Air Putih','Susu/Keju/Yogurt','Minuman/Kaldu/Jus','Sayur & Buah','Protein Hewani','Kacang/Snack']
        c1,c2=st.columns([2,1])
        with c1:
            fig=bar_multi(df,col,pats_i,lbls_i,'📊 Konsumsi Ibu','#7C3AED')
            if fig: st.plotly_chart(fig,use_container_width=True); del fig
        with c2:
            dds_vals=df[col].apply(lambda x: sum(1 for p in pats_i if p.lower() in str(x).lower()))
            mdd=(dds_vals>=5).sum()
            st.markdown(f"""<div class="card" style="font-size:1rem"><b>📋 Keragaman Pangan Ibu (6 kelompok)</b><br><br>
            ≥ 5: <b>{mdd} ({fmt(pct(mdd,n))})</b><br>< 5: <b>{n-mdd} ({fmt(pct(n-mdd,n))})</b><br><br>
            Rerata: <b>{dds_vals.mean():.1f}</b></div>""",unsafe_allow_html=True)

    st.markdown('<div class="sh">📊 Frekuensi Makan Ibu</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    for key,title,clr,container in [('frek_lengkap','Makan Lengkap','#0D9488',c1),('frek_kudapan','Kudapan','#8B5CF6',c2)]:
        col=g(df,key)
        if col:
            with container:
                # PERBAIKAN: Hanya tambahkan threshold untuk 'Makan Lengkap', tidak untuk 'Kudapan'
                if 'Lengkap' in title:
                    # Threshold di index 3 (antara '2' dan '3')
                    fig,m,mn,s=dist_bar(df[col],[0,1,2,3,4,5,8],
                                       ['0','1','2','3','4','≥ 5'],
                                       f'📊 {title} (24 jam)',clr,3,'< 3x/hari')
                    st.plotly_chart(fig,use_container_width=True); del fig
                    kurang=(s<3).sum()
                    st.markdown(f'<div class="card">⚠️ Makan < 3×: <b>{kurang}</b> ({fmt(pct(kurang,len(s)))})</div>',unsafe_allow_html=True)
                else:
                    # Kudapan - tanpa garis threshold
                    fig,m,mn,s=dist_bar(df[col],[0,1,2,3,4,5,8],
                                       ['0','1','2','3','4','≥ 5'],
                                       f'📊 {title} (24 jam)',clr)
                    st.plotly_chart(fig,use_container_width=True); del fig
    gc.collect()

# ===== MAIN =====
def main():
    st.markdown("""<div class="dh"><h1>📋 Dashboard Indepth Stunting</h1>
    <p>Kelurahan Satimpo, Kec. Bontang Selatan, Kota Bontang — Kalimantan Timur | Juni 2026</p></div>""", unsafe_allow_html=True)
    st.markdown("""<div style="background:linear-gradient(135deg,#F0FDFA,#CCFBF1);border:1px solid #5EEAD4;border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1rem">
    <div style="font-size:1.05rem;font-weight:600;color:#134E4A;margin-bottom:.6rem">📌 Tentang Penelitian</div>
    <div style="font-size:.95rem;color:#1E293B;line-height:1.7">
    Indepth survey terhadap <b>seluruh 48 balita stunting</b> di Kel. Satimpo (Juni 2026).
    Dari 347 balita ditimbang, <b>48 teridentifikasi stunting (13,83%)</b> — seluruhnya menjadi responden (<i>total sampling</i>).
    Referensi: SSGI 2024.</div></div>""", unsafe_allow_html=True)

    try: 
        df = load_data()
    except Exception as e: 
        st.error(f"⚠️ File tidak ditemukan: {e}")
        st.stop()

    # === SIDEBAR: Filter RT & Posyandu ===
    st.sidebar.markdown('<h2 style="color:#0F766E;text-align:center;font-size:1.2rem">🔍 Filter Data</h2>', unsafe_allow_html=True)

    rt_col = col_find(df, 'RT')
    pos_col = col_find(df, 'Posyandu')

    if rt_col:
        rt_list = sorted(df[rt_col].dropna().unique(), key=lambda x: int(x) if str(x).isdigit() else 0)
        sel_rt = st.sidebar.multiselect("🏘️ RT", options=rt_list, default=rt_list)
        df = df[df[rt_col].isin(sel_rt)]

    if pos_col:
        pos_list = sorted(df[pos_col].dropna().unique())
        sel_pos = st.sidebar.multiselect("🏥 Posyandu", options=pos_list, default=pos_list)
        df = df[df[pos_col].isin(sel_pos)]

    st.sidebar.markdown("---")
    st.sidebar.markdown('<h2 style="color:#0F766E;text-align:center;font-size:1.2rem">📋 Info</h2>', unsafe_allow_html=True)
    st.sidebar.markdown(f"**Responden tampil:** {len(df)}\n\n**Desain:** Total sampling\n\n**Referensi:** SSGI 2024")
    st.sidebar.markdown("---")
    st.sidebar.info("**Prevalensi Stunting Satimpo:**\n48 balita stunting dari 347 balita ditimbang (13,83%)\n\n**Prevalensi Stunting Kota Bontang:**\n1.389 dari 9.884 balita ditimbang (14,05%)\n\n**Peringkat Satimpo:**\nUrutan ke-8 dari 15 kelurahan di Kota Bontang")

    if len(df) == 0:
        st.warning("⚠️ Tidak ada data yang sesuai filter. Silakan ubah pilihan RT atau Posyandu.")
        st.stop()

    # === MENU NAVIGASI INTERAKTIF ===
    if 'menu_aktif' not in st.session_state:
        st.session_state.menu_aktif = "ringkasan"
    
    menu_data = [
        {"key": "ringkasan", "icon": "📊", "label": "Ringkasan"},
        {"key": "kehamilan", "icon": "🤰", "label": "Riwayat Kehamilan"},
        {"key": "imunisasi", "icon": "💉", "label": "Imunisasi"},
        {"key": "asi_mpasi", "icon": "🍼", "label": "ASI & MPASI"},
        {"key": "pengasuhan", "icon": "🏥", "label": "Pengasuhan & Determinan"},
        {"key": "konsumsi", "icon": "🍽️", "label": "Konsumsi Ibu"},
    ]
    
    cols = st.columns(len(menu_data))
    
    for col, item in zip(cols, menu_data):
        with col:
            is_active = st.session_state.menu_aktif == item["key"]
            
            if is_active:
                st.markdown(f"""
                <div class="menu-btn active">
                    <span class="menu-icon">{item['icon']}</span>
                    <span class="menu-label">{item['label']}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button(
                    f"{item['icon']}\n{item['label']}",
                    key=f"menu_{item['key']}",
                    use_container_width=True,
                    type="secondary"
                ):
                    st.session_state.menu_aktif = item["key"]
                    st.rerun()
    
    st.markdown("---")
    
    if st.session_state.menu_aktif == "ringkasan":
        page_ringkasan(df)
    elif st.session_state.menu_aktif == "kehamilan":
        page_kehamilan(df)
    elif st.session_state.menu_aktif == "imunisasi":
        page_imunisasi(df)
    elif st.session_state.menu_aktif == "asi_mpasi":
        page_asi_mpasi(df)
    elif st.session_state.menu_aktif == "pengasuhan":
        page_pengasuhan(df)
    elif st.session_state.menu_aktif == "konsumsi":
        page_konsumsi_ibu(df)
    
    st.markdown("---")
    st.markdown('<div style="text-align:center;color:#64748B;font-size:.9rem">Dashboard Indepth Stunting — Kel. Satimpo, Kota Bontang | Juni 2026 | Referensi: SSGI 2024</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
