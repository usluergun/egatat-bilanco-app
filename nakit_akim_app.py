import streamlit as st
import os
import json
import datetime

# Türkçe para formatı fonksiyonu
def turkce_para_format(x):
    s = f"{x:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

KALEM_ACIKLAMALARI = {
    "Dönem Net Kârı (Zararı)": "Vergi sonrası net kâr veya zarar.",
    "Amortisman ve İtfa Payları": "Varlıkların yıllık yıpranma ve değer düşüklüğü payları.",
    "Karşılıklar": "Kıdem tazminatı, dava, şüpheli alacak gibi ayrılan karşılıklar.",
    "Faiz Giderleri": "Banka, kredi, tahvil gibi finansman kaynaklarına ödenen faizler.",
    "Faiz Gelirleri": "Banka mevduatlarından ve alacaklardan tahsil edilen faizler.",
    "Alacaklardaki Değişim": "Müşteriden tahsilatlar, senetler, çekler.",
    "Stoklardaki Değişim": "Hammadde, mamul, yarı mamul, ticari mal stok hareketleri.",
    "Borçlardaki Değişim": "Tedarikçi, satıcı, kredi gibi kısa vadeli borçlardaki değişiklikler.",
    "Diğer Faaliyet Gelir/Giderleri": "Sigorta, komisyon, kur farkı, diğer olağan gelir/giderler.",
    "Maddi Duran Varlık Alımları": "Bina, arsa, makine, araç gibi yatırımlara yapılan ödemeler.",
    "Maddi Duran Varlık Satışları": "Bu varlıkların satışıyla elde edilen nakit.",
    "Diğer Yatırım Giriş/Çıkışları": "Hisse alımı/satımı, finansal yatırımlar, iştirakler.",
    "Kredi Kullanımı": "Banka ve finansal kurumlardan alınan yeni krediler.",
    "Kredi Geri Ödemeleri": "Mevcut kredilerin ana para ve faiz ödemeleri.",
    "Sermaye Artırımı": "Ortaklarca işletmeye aktarılan yeni sermaye/nakit.",
    "Temettü Ödemeleri": "Kar payı dağıtımları, ortaklara yapılan ödemeler.",
    "Diğer Finansman Giriş/Çıkışları": "Leasing, finansal kiralama, diğer özel finansman işlemleri."
}

# --- Nakit Akım Kalemleri Açıklamaları (Sidebar) ---
st.sidebar.markdown("## Nakit Akım Kalemleri Açıklamaları")

st.sidebar.markdown("**A. Faaliyetlerden Sağlanan Nakit Akımları**")
st.sidebar.markdown("""
- **Dönem Net Kârı (Zararı):** Vergi sonrası net kâr veya zarar.
- **Amortisman ve İtfa Payları:** Varlıkların yıllık yıpranma ve değer düşüklüğü payları.
- **Karşılıklar:** Kıdem tazminatı, dava, şüpheli alacak gibi ayrılan karşılıklar.
- **Faiz Giderleri:** Banka, kredi, tahvil gibi finansman kaynaklarına ödenen faizler.
- **Faiz Gelirleri:** Banka mevduatlarından ve alacaklardan tahsil edilen faizler.
- **Alacaklardaki Değişim:** Müşteriden tahsilatlar, senetler, çekler.
- **Stoklardaki Değişim:** Hammadde, mamul, yarı mamul, ticari mal stok hareketleri.
- **Borçlardaki Değişim:** Tedarikçi, satıcı, kredi gibi kısa vadeli borçlardaki değişiklikler.
- **Diğer Faaliyet Gelir/Giderleri:** Sigorta, komisyon, kur farkı, diğer olağan gelir/giderler.
""")

st.sidebar.markdown("**B. Yatırım Faaliyetlerinden Nakit Akımları**")
st.sidebar.markdown("""
- **Maddi Duran Varlık Alımları:** Bina, arsa, makine, araç gibi yatırımlara yapılan ödemeler.
- **Maddi Duran Varlık Satışları:** Bu varlıkların satışıyla elde edilen nakit.
- **Diğer Yatırım Giriş/Çıkışları:** Hisse alımı/satımı, finansal yatırımlar, iştirakler.
""")

st.sidebar.markdown("**C. Finansman Faaliyetlerinden Nakit Akımları**")
st.sidebar.markdown("""
- **Kredi Kullanımı:** Banka ve finansal kurumlardan alınan yeni krediler.
- **Kredi Geri Ödemeleri:** Mevcut kredilerin ana para ve faiz ödemeleri.
- **Sermaye Artırımı:** Ortaklarca işletmeye aktarılan yeni sermaye/nakit.
- **Temettü Ödemeleri:** Kar payı dağıtımları, ortaklara yapılan ödemeler.
- **Diğer Finansman Giriş/Çıkışları:** Leasing, finansal kiralama, diğer özel finansman işlemleri.
""")

# --- Ana kalem-alt kalem eşleşmeleri (Bilanço ile uyumlu) ---
ALT_KALEMLER = {
    "Kasa": ["Şube kasası", "Merkez kasa"],
    "Bankalar": ["Banka TL Hesabı", "Banka Dolar Hesabı", "Banka POS"],
    "Ticari Alacaklar": ["Müşteri Çekleri", "Senetler", "Açık Alacaklar"],
    # Buraya bilanço sistemindeki tüm ana ve alt kalemleri ekle!
}

def get_ana_kalem_toplam(bilanco_json, ana_kalem, alt_kalemler):
    return sum([
        bilanco_json.get(f"{ana_kalem}_{alt}", 0.0)
        for alt in alt_kalemler.get(ana_kalem, [])
    ])

def bilanco_fark(bilanco, key, yil, ay, onceki_bilanco):
    simdiki = bilanco.get(key, 0.0)
    onceki = onceki_bilanco.get(key, 0.0) if onceki_bilanco else 0.0
    return simdiki - onceki

def otomatik_deger(kalem, bilanco, yil, ay, onceki_bilanco):
    key = BILANCO_KEYLER.get(kalem)
    if kalem in [
        "Alacaklardaki Değişim", "Stoklardaki Değişim", "Borçlardaki Değişim",
        "Maddi Duran Varlık Alımları", "Maddi Duran Varlık Satışları",
        "Kredi Kullanımı", "Kredi Geri Ödemeleri"
    ]:
        return bilanco_fark(bilanco, key, yil, ay, onceki_bilanco)
    else:
        return bilanco.get(key, 0.0) if key else 0.0

# --- Bilanço dosyası okuma fonksiyonu ---
def get_bilanco_tutar(kullanici, yil, ay):
    """
    Kayıtlı bilanço dosyasını okur ve dict olarak döner.
    Dosya adı örneği: bilanco_ergun_2025-07.json
    """
    dosya_adi = f"bilanco_{kullanici}_{yil}-{ay}.json"
    if os.path.exists(dosya_adi):
        with open(dosya_adi, "r") as f:
            return json.load(f)
    else:
        return {}  # Dosya yoksa boş dict
# --- BİLANÇO-NAKİT AKIM KEY EŞLEŞMESİ ---
BILANCO_KEYLER = {
    "Dönem Net Kârı (Zararı)":           "Net_Kar_Zarar",
    "Amortisman ve İtfa Payları":        "Amortisman",
    "Karşılıklar":                       "Karsiliklar",
    "Faiz Giderleri":                    "Faiz_Giderleri",
    "Faiz Gelirleri":                    "Faiz_Gelirleri",
    "Alacaklardaki Değişim":             "Ticari_Alacaklar",  # FARK alınacak!
    "Stoklardaki Değişim":               "Stoklar",           # FARK alınacak!
    "Borçlardaki Değişim":               "Ticari_Borclar",    # FARK alınacak!
    "Maddi Duran Varlık Alımları":       "Maddi_Duran_Varliklar", # FARK alınacak!
    "Maddi Duran Varlık Satışları":      "Maddi_Duran_Varlik_Satis", # FARK alınacak!
    "Kredi Kullanımı":                   "Krediler",          # FARK alınacak!
    "Kredi Geri Ödemeleri":              "Kredi_Geri_Odemeleri", # FARK alınacak!
    "Sermaye Artırımı":                  "Sermaye_Artirimi",
    "Temettü Ödemeleri":                 "Temettu_Odemeleri",
    "Diğer Faaliyet Gelir/Giderleri":    "Diger_Faaliyet_Gelir_Gider",
    "Diğer Yatırım Giriş/Çıkışları":     "Diger_Yatirim",
    "Diğer Finansman Giriş/Çıkışları":   "Diger_Finansman",
    "Dönem Başı Nakit":                  "Kasa"
}


st.set_page_config(page_title="Kurumsal Nakit Akım Tablosu", layout="wide")
st.markdown("<h2 style='text-align:center;'>EGE TAT FIRIN Kurumsal Nakit Akım Tablosu</h2>", unsafe_allow_html=True)

# Kullanıcı adı sabitlenmiş (otomatik)
kullanici = "ergun"

# Ay ve yıl seçimi (önceki haliyle aynı)
col1, col2 = st.columns(2)
with col1:
    yil = st.selectbox("Yıl", options=[2024, 2025, 2026], index=1)
with col2:
    ay = st.selectbox("Ay", options=[f"{i:02d}" for i in range(1,13)], index=datetime.datetime.now().month-1)

# Bilanço dosyasından başlangıç kasası çek ve EN ÜSTE yaz
bilanco_tutar = get_bilanco_tutar(kullanici, yil, ay)
onceki_bilanco = get_bilanco_tutar(kullanici, yil, f"{int(ay)-1:02d}") if int(ay) > 1 else {}
donem_basi_nakit = get_ana_kalem_toplam(bilanco_tutar, "Kasa", ALT_KALEMLER)
st.info(f"Başlangıç Kasası (Bilanço verisinden): {donem_basi_nakit:,.2f} ₺")

st.markdown("---")
st.markdown("### Profesyonel Nakit Akım Tablosu (Otomatik Bilanço Bağlantılı)")

# -- GRUPLU NAKİT AKIM PANELİ --
NAKIT_AKIM_GRUPLARI = {
    "A. Faaliyetlerden Sağlanan Nakit Akımları": [
        "Dönem Net Kârı (Zararı)",
        "Amortisman ve İtfa Payları",
        "Karşılıklar",
        "Faiz Giderleri",
        "Faiz Gelirleri",
        "Alacaklardaki Değişim",
        "Stoklardaki Değişim",
        "Borçlardaki Değişim",
        "Diğer Faaliyet Gelir/Giderleri"
    ],
    "B. Yatırım Faaliyetlerinden Nakit Akımları": [
        "Maddi Duran Varlık Alımları",
        "Maddi Duran Varlık Satışları",
        "Diğer Yatırım Giriş/Çıkışları"
    ],
    "C. Finansman Faaliyetlerinden Nakit Akımları": [
        "Kredi Kullanımı",
        "Kredi Geri Ödemeleri",
        "Sermaye Artırımı",
        "Temettü Ödemeleri",
        "Diğer Finansman Giriş/Çıkışları"
    ]
}


# --- Karşılaştırmalı Dönem Seçimi ---
st.markdown("### 🔄 Karşılaştırmalı Dönem Paneli (3 Sütunlu)")

col_1, col_2, col_3, col_4 = st.columns([2, 1, 1, 1])
with col_1:
    st.write("Kalem")
with col_2:
    d_yil1 = st.selectbox("1. Dönem Yıl", options=[2024,2025,2026], index=1, key="d_yil1")
    d_ay1 = st.selectbox("1. Dönem Ay", options=[f"{i:02d}" for i in range(1,13)], index=0, key="d_ay1")
with col_3:
    d_yil2 = st.selectbox("2. Dönem Yıl", options=[2024,2025,2026], index=1, key="d_yil2")
    d_ay2 = st.selectbox("2. Dönem Ay", options=[f"{i:02d}" for i in range(1,13)], index=1, key="d_ay2")
with col_4:
    st.write("Fark (2. - 1.)")

def get_nakit_akim_json(yil, ay):
    dosya = f"nakit_akim_{kullanici}_{yil}-{ay}.json"
    if os.path.exists(dosya):
        with open(dosya, "r") as f:
            return json.load(f)
    return {}

nakit_bir = get_nakit_akim_json(d_yil1, d_ay1)
nakit_iki = get_nakit_akim_json(d_yil2, d_ay2)

nakit_akim_giris = {}
toplamlar = {}

for grup, kalemler in NAKIT_AKIM_GRUPLARI.items():
    st.markdown(f"#### {grup}")

    # Sütun başlıkları (tek satır)
    cols_header = st.columns([2, 2.3, 1, 0.7, 0.7, 0.7])
    cols_header[0].markdown("**Kalem Adı**")
    cols_header[1].markdown("**Açıklama**")
    cols_header[2].markdown("**Cari Dönem Girişi**")
    cols_header[3].markdown(f"**{d_yil1}-{d_ay1}**")
    cols_header[4].markdown(f"**{d_yil2}-{d_ay2}**")
    cols_header[5].markdown("**Fark (2.-1.)**")

    for kalem in kalemler:
        cols = st.columns([2, 2.3, 1, 0.7, 0.7, 0.7])
        cols[0].write(f"**{kalem}**")
        cols[1].write(KALEM_ACIKLAMALARI.get(kalem, ""))
        v1 = nakit_bir.get("nakit_akim_giris", {}).get(kalem, 0.0)
        v2 = nakit_iki.get("nakit_akim_giris", {}).get(kalem, 0.0)
        fark = v2 - v1
        # Yeni: Sadece text_input ile değer gir, yanında TL formatlı gösterim
        otomatik = otomatik_deger(kalem, bilanco_tutar, yil, ay, onceki_bilanco)
        default_str = f"{otomatik:.2f}".replace(".", ",")
        cari_str = cols[2].text_input(
            "",
            value=default_str,
            key=f"nakit_{kalem}",
            label_visibility="collapsed"
        )
        # Türkçe para formatı gösterimi
        try:
            # Nokta ve virgül temizleme: 1.000.000,50 -> 1000000.50
            temiz = cari_str.replace(".", "").replace(",", ".")
            cari_giris = float(temiz)
        except Exception:
            cari_giris = 0.0
        cols[2].markdown(
            f"<span style='color:#009900;font-weight:bold;'>{turkce_para_format(cari_giris)} ₺</span>",
            unsafe_allow_html=True
        )
        nakit_akim_giris[kalem] = cari_giris
        cols[3].write(turkce_para_format(v1))
        cols[4].write(turkce_para_format(v2))
        cols[5].write(turkce_para_format(fark))

net_nakit_akim = sum(toplamlar.values())
donem_sonu_nakit = donem_basi_nakit + net_nakit_akim
st.success(f"**Dönem Sonu Nakit ve Nakit Benzerleri: {donem_sonu_nakit:,.2f} ₺**")

# Kaydet
dosya_adi = f"nakit_akim_{kullanici}_{yil}-{ay}.json"
if st.button("Nakit Akımını Kaydet"):
    kayit = {
        "kullanici": kullanici,
        "yil": yil,
        "ay": ay,
        "baslangic_kasa": donem_basi_nakit,
        "bitis_kasa": donem_sonu_nakit,
        "nakit_akim_giris": nakit_akim_giris,
        "toplam": net_nakit_akim,
        "tarih": str(datetime.datetime.now())
    }
    with open(dosya_adi, "w") as f:
        json.dump(kayit, f, ensure_ascii=False, indent=2)
    st.success("Nakit akım kaydedildi!")

# --- Bilanço ve Nakit Akım Tablosu Uyum Kontrolü ---
# Dönem sonu bilanço nakit (Kasa + Bankalar toplamı)
bilanco_nakit_sonu = get_ana_kalem_toplam(bilanco_tutar, "Kasa", ALT_KALEMLER) + \
                     get_ana_kalem_toplam(bilanco_tutar, "Bankalar", ALT_KALEMLER)

st.markdown("### 🚦 Bilanço & Nakit Akım Uyum Kontrolü")
if abs(donem_sonu_nakit - bilanco_nakit_sonu) < 1:
    st.success(f"Nakit akım ve bilanço uyumlu. [Nakit akım tablosu dönem sonu: {donem_sonu_nakit:,.2f} ₺] = [Bilanço sonu nakit: {bilanco_nakit_sonu:,.2f} ₺]")
else:
    st.error(f"UYARI: Nakit akım tablosu dönem sonu ({donem_sonu_nakit:,.2f} ₺) ile bilanço sonu nakit ({bilanco_nakit_sonu:,.2f} ₺) uyuşmuyor!")

import pandas as pd

#
# --- Bilanço ve Nakit Akım Tablosu Uyum Kontrolü ---
#
# Otomatik çekilen kalemlerin de dönemsel fark kontrolü
def fark_kontrol(kalem, ana_kalem):
    try:
        this_month = get_ana_kalem_toplam(bilanco_tutar, ana_kalem, ALT_KALEMLER)
        prev_month = get_ana_kalem_toplam(onceki_bilanco, ana_kalem, ALT_KALEMLER)
        net_fark = this_month - prev_month
        girilen = nakit_akim_giris.get(kalem, 0.0)
        if abs(girilen - net_fark) < 1:
            st.info(f"✔️ {kalem}: Nakit akım ve bilanço farkı uyumlu. ({girilen:,.2f} ₺)")
        else:
            st.warning(f"⚠️ {kalem}: Nakit akım tablosundaki değer ({girilen:,.2f} ₺), bilanço farkı ({net_fark:,.2f} ₺) ile uyuşmuyor!")
    except Exception as e:
        st.warning(f"{kalem} kontrolü yapılamadı: {e}")

st.markdown("#### Otomatik Kalem Uyumları:")
fark_kontrol("Alacaklardaki Değişim", "Ticari Alacaklar")
fark_kontrol("Stoklardaki Değişim", "Stoklar")
fark_kontrol("Borçlardaki Değişim", "Ticari Borçlar")

# --- Rasyolar ve Grafik Bölümü ---
st.markdown("### 📊 Rasyolar ve Grafikler")

# Örnek: Net Kâr Marjı
net_kar = nakit_akim_giris.get("Dönem Net Kârı (Zararı)", 0.0)
toplam_gelir = 1000000  # Sabit veya kullanıcıdan alınabilir
net_kar_marji = (net_kar / toplam_gelir) * 100 if toplam_gelir != 0 else 0
st.write(f"**Net Kâr Marjı:** {net_kar_marji:.2f}%")
st.caption("Net Kâr Marjı = Dönem Net Kârı (Zararı) / Toplam Gelir")

# 1. Toplamları hesapla
faaliyet_toplam = sum([nakit_akim_giris.get(k, 0.0) for k in NAKIT_AKIM_GRUPLARI["A. Faaliyetlerden Sağlanan Nakit Akımları"]])
yatirim_toplam = sum([nakit_akim_giris.get(k, 0.0) for k in NAKIT_AKIM_GRUPLARI["B. Yatırım Faaliyetlerinden Nakit Akımları"]])
finansman_toplam = sum([nakit_akim_giris.get(k, 0.0) for k in NAKIT_AKIM_GRUPLARI["C. Finansman Faaliyetlerinden Nakit Akımları"]])
net_nakit_akim = faaliyet_toplam + yatirim_toplam + finansman_toplam

# 2. Rasyoları hesapla
faaliyet_orani = (faaliyet_toplam / net_nakit_akim) * 100 if net_nakit_akim != 0 else 0
yatirim_orani = (yatirim_toplam / net_nakit_akim) * 100 if net_nakit_akim != 0 else 0
finansman_orani = (finansman_toplam / net_nakit_akim) * 100 if net_nakit_akim != 0 else 0

# 3. Net Kâr Marjı'nın altına ekle (st.write ile!)
st.write(f"**Faaliyet Nakit Oranı:** {faaliyet_orani:.2f}%")
st.caption("Faaliyet Nakit Oranı = Faaliyetlerden Sağlanan Nakit Akımları / Net Nakit Akım")
st.write(f"**Yatırım Nakit Oranı:** {yatirim_orani:.2f}%")
st.caption("Yatırım Nakit Oranı = Yatırım Faaliyetlerinden Nakit Akımları / Net Nakit Akım")
st.write(f"**Finansman Nakit Oranı:** {finansman_orani:.2f}%")
st.caption("Finansman Nakit Oranı = Finansman Faaliyetlerinden Nakit Akımları / Net Nakit Akım")

# Örnek grafik (basit bar chart)
# Grafik için kullanılacak veri kaynağını belirle:
import matplotlib.pyplot as plt
if nakit_akim_giris and any(nakit_akim_giris.values()):
    grafik_veri = nakit_akim_giris
elif os.path.exists(dosya_adi):
    with open(dosya_adi, "r") as f:
        veri = json.load(f)
    grafik_veri = veri.get("nakit_akim_giris", {})
else:
    grafik_veri = {}

# Grafik çizimi:
kalemler = list(grafik_veri.keys())
tutarlar = [grafik_veri[k] for k in kalemler]

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(kalemler, tutarlar, color='skyblue')
ax.set_xlabel("Tutar (₺)")
ax.set_title("Nakit Akım Kalemleri Grafiği")
st.pyplot(fig)

# Son kayıt varsa göster (tablo + CSV indirme + JSON expander)
if os.path.exists(dosya_adi):
    st.markdown("---")
    st.markdown("#### Kayıtlı Nakit Akım Verisi (Tablolu):")
    with open(dosya_adi, "r") as f:
        veri = json.load(f)

    # Nakit akım girişlerini DataFrame'e çevir
    nakit_akim_dict = veri.get("nakit_akim_giris", {})
    df = pd.DataFrame(list(nakit_akim_dict.items()), columns=["Kalem", "Tutar"])
    df["Tutar"] = df["Tutar"].astype(float)
    df["Tutar"] = df["Tutar"].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    df["Açıklama"] = df["Kalem"].map(KALEM_ACIKLAMALARI)
    df = df[["Kalem", "Açıklama", "Tutar"]]

    # DataFrame'i görsel olarak göster
    st.dataframe(df, use_container_width=True)

    # CSV olarak indirme butonu ekle
    csv = df.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button(
        label="Kayıtlı Nakit Akım Tablosunu CSV Olarak İndir",
        data=csv,
        file_name=f"nakit_akim_{kullanici}_{yil}-{ay}.csv",
        mime="text/csv"
    )

    # Eski JSON görünümünü Expander ile isteğe bağlı göster
    with st.expander("JSON Kayıt (detay için):"):
        st.json(veri)

# --- Diğer Tabloya Geç ---
st.markdown("---")
st.markdown("### 📊 Diğer Tabloya Geç")
if st.button("Bilanço Tablosuna Geç"):
    st.info("Bilanço tablosuna geçmek için ana menüden veya doğrudan bilanco_app.py dosyasını çalıştırabilirsiniz. (Not: Streamlit çoklu app geçişini otomatik olarak desteklemez, ancak bir başlatıcı veya ana menü üzerinden geçiş yapılabilir.)")
    st.write("Terminal veya komut satırında şunu çalıştırabilirsin:")
    st.code("streamlit run bilanco_app.py")
st.markdown("""
[👉 Bilanço Tablosuna Gitmek İçin Tıklayın](http://localhost:8501/)
""")