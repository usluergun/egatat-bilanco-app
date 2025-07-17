import plotly.express as px
import glob
def finansal_rasyolar(ana_kalem_tutar):
    donen_varliklar = sum([ana_kalem_tutar.get(x, 0) for x in [
        "Kasa", "Bankalar", "Ticari Alacaklar", "Stoklar", "Diğer Dönen Varlıklar"
    ]])
    kisa_vadeli_borclar = sum([ana_kalem_tutar.get(x, 0) for x in [
        "Ticari Borçlar", "Çekler", "SGK", "KDV", "Muhtasar", "Diğer Kısa Vadeli Borçlar"
    ]])
    stoklar = ana_kalem_tutar.get("Stoklar", 0)
    uzun_vadeli_borclar = ana_kalem_tutar.get("Uzun Vadeli Borçlar", 0)
    ozkaynak = sum([ana_kalem_tutar.get(x, 0) for x in [
        "Ödenmiş Sermaye", "Geçmiş Yıllar Kar/Zarar", "Dönem Net Kar/Zarar"
    ]])
    cari_oran = donen_varliklar / kisa_vadeli_borclar if kisa_vadeli_borclar > 0 else 0
    likidite_orani = (donen_varliklar - stoklar) / kisa_vadeli_borclar if kisa_vadeli_borclar > 0 else 0
    toplam_borclar = kisa_vadeli_borclar + uzun_vadeli_borclar
    borc_ozkaynak_orani = toplam_borclar / ozkaynak if ozkaynak > 0 else 0

    return {
        "Cari Oran": cari_oran,
        "Likidite Oranı": likidite_orani,
        "Borç/Özkaynak Oranı": borc_ozkaynak_orani
    }

def rasyo_uyari_degeri(isim, deger):
    if isim == "Cari Oran":
        if deger < 1:
            renk, durum = "red", "Riskli"
        elif deger < 1.5:
            renk, durum = "orange", "İdare eder"
        else:
            renk, durum = "green", "Güvenli"
    elif isim == "Likidite Oranı":
        if deger < 0.8:
            renk, durum = "red", "Riskli"
        elif deger < 1:
            renk, durum = "orange", "Düşük"
        else:
            renk, durum = "green", "İyi"
    elif isim == "Borç/Özkaynak Oranı":
        if deger > 2:
            renk, durum = "red", "Yüksek Borçluluk"
        elif deger > 1:
            renk, durum = "orange", "Dikkat"
        else:
            renk, durum = "green", "Sağlıklı"
    else:
        renk, durum = "gray", ""
    return renk, durum
def tl_format(tutar):
    # Nokta binlik, virgül ondalık, iki hane
    return '{:,.2f}'.format(tutar).replace(',', 'X').replace('.', ',').replace('X', '.')
import streamlit as st
import pandas as pd
import json
import os
import datetime
from st_aggrid import AgGrid, GridOptionsBuilder

def get_kilit_durumu(kullanici, yil, ay):
    kilit_dosya = f"bilanco_{kullanici}_{yil}-{ay}_kilit.json"
    if os.path.exists(kilit_dosya):
        with open(kilit_dosya, "r") as f:
            data = json.load(f)
        return data.get("kilit", False)
    return False

def set_kilit_durumu(kullanici, yil, ay, durum):
    kilit_dosya = f"bilanco_{kullanici}_{yil}-{ay}_kilit.json"
    with open(kilit_dosya, "w") as f:
        json.dump({"kilit": durum}, f)

if "username" not in st.session_state:
    st.session_state["username"] = ""

if st.session_state["username"] == "":
    st.title("Kullanıcı Girişi")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        USERS = {
            "ergun": "1234",
            "ismail": "1234"
        }
        if username in USERS and password == USERS[username]:
            st.session_state["username"] = username
            st.success("Giriş başarılı!")
            st.rerun()
        else:
            st.error("Hatalı kullanıcı adı veya şifre!")
    st.stop()
else:
    kullanici = st.session_state["username"]
    today = datetime.date.today()
    st.subheader("Bilanço Dönemi Seçimi", divider="gray")
    col1, col2 = st.columns([1, 1])
    with col1:
        yil = st.selectbox("Yıl", options=[y for y in range(2023, today.year+2)], index=(today.year-2023), label_visibility="collapsed")
    with col2:
        ay = st.selectbox("Ay", options=[f"{i:02d}" for i in range(1,13)], index=today.month-1, label_visibility="collapsed")

    kilitli = get_kilit_durumu(kullanici, yil, ay)

    col3, col4 = st.columns([1,1])
    with col3:
        if not kilitli:
            if st.button("Bu Ayı Kilitle (Kapanış)"):
                set_kilit_durumu(kullanici, yil, ay, True)
                st.success(f"{yil}/{ay} dönemi kilitlendi.")
                st.experimental_rerun()
        else:
            st.button("Bu Ayı Kilitle (Kapanış)", disabled=True)
    with col4:
        if kilitli:
            if st.button("Kilit Aç (Düzenleme Serbest)"):
                set_kilit_durumu(kullanici, yil, ay, False)
                st.success(f"{yil}/{ay} dönemi kilidi açıldı.")
                st.experimental_rerun()
        else:
            st.button("Kilit Aç (Düzenleme Serbest)", disabled=True)

    donem = f"{yil}-{ay}"
    st.markdown(f"<h3 style='text-align:center; margin-bottom: 0.2em;'>BİLANÇO DÖNEMİ: {yil} / {ay}</h3>", unsafe_allow_html=True)
    KAYIT_DOSYASI = f"bilanco_{kullanici}_{donem}.json"

    def kaydet_bilanco_state():
        with open(KAYIT_DOSYASI, "w") as f:
            json.dump(dict(st.session_state), f)

    def yukle_bilanco_state():
        # Sadece ilk yüklemede çalışsın!
        if "state_loaded" not in st.session_state:
            if os.path.exists(KAYIT_DOSYASI):
                with open(KAYIT_DOSYASI, "r") as f:
                    kayit = json.load(f)
                    for k, v in kayit.items():
                        if (
                            not k.startswith("username")
                            and not k.endswith("_dosya_detay")
                            and not k.endswith("_aciklama_detay")
                            and not k.endswith("_audit_detay")
                        ):
                            st.session_state[k] = v
            st.session_state["state_loaded"] = True

    yukle_bilanco_state()

    st.markdown("<h1 style='text-align:center; margin-bottom:0.2em;'>EGE TAT FIRIN Kurumsal Bilanço Otomasyonu</h1>", unsafe_allow_html=True)

    # --- Bilanço Kalemleri ---
    bilanco_kalemleri = [
        "Kasa", "Bankalar", "Ticari Alacaklar", "Stoklar", "Diğer Dönen Varlıklar",
        "Maddi Duran Varlıklar", "Maddi Olmayan Duran Varlıklar", "Diğer Duran Varlıklar",
        "Ticari Borçlar", "Çekler", "SGK", "KDV", "Muhtasar", "Diğer Kısa Vadeli Borçlar",
        "Uzun Vadeli Borçlar", "Ödenmiş Sermaye", "Geçmiş Yıllar Kar/Zarar", "Dönem Net Kar/Zarar"
    ]

    kalem_aciklamalari = {
        "Kasa": "Şube kasaları, merkez kasa, döviz kasa",
        "Bankalar": "Banka TL/vadesiz/vadeli/döviz hesapları",
        "Ticari Alacaklar": "Müşteri alacakları, senetler, çekler",
        "Stoklar": "Mamul, yarı mamul, hammadde, ticari mal",
        "Diğer Dönen Varlıklar": "Peşin ödenen giderler, vergi alacakları",
        "Maddi Duran Varlıklar": "Bina, arsa, araç, makine, demirbaş",
        "Maddi Olmayan Duran Varlıklar": "Marka, patent, yazılım, know-how",
        "Diğer Duran Varlıklar": "Verilen depozitolar, uzun vadeli alacaklar",
        "Ticari Borçlar": "Tedarikçi borçları, satıcılar, alınan çekler",
        "Çekler": "Ödenecek çekler, portföydeki çekler",
        "SGK": "SGK prim borçları",
        "KDV": "Hesaplanan ve indirilecek KDV",
        "Muhtasar": "Muhtasar stopaj borçları",
        "Diğer Kısa Vadeli Borçlar": "Personele borçlar, ödenecek diğer vergiler",
        "Uzun Vadeli Borçlar": "Banka kredileri, uzun vadeli ticari borçlar",
        "Ödenmiş Sermaye": "Ortaklara ait ödenmiş sermaye",
        "Geçmiş Yıllar Kar/Zarar": "Geçmiş yıl karı/zararı",
        "Dönem Net Kar/Zarar": "Bu yılın net karı veya zararı"
    }

    st.sidebar.header("Bilanço Kalemleri Açıklamaları")
    for kalem in bilanco_kalemleri:
        st.sidebar.markdown(f"**{kalem}:** {kalem_aciklamalari.get(kalem, '')}")

    alt_kalemler = {
        "Kasa": ["Şube kasası", "Merkez kasa", "Döviz kasa"],
        "Bankalar": ["Banka TL Hesabı", "Banka USD Hesabı", "Banka EUR Hesabı"],
        "Ticari Alacaklar": ["Müşteri alacakları", "Senet alacakları", "Çek alacakları"],
        "Stoklar": ["Mamul", "Yarı mamul", "Hammadde", "Ticari mal", "Yardımcı malzeme"],
        "Diğer Dönen Varlıklar": ["Peşin ödenen giderler", "Vergi alacakları", "Verilen depozito ve teminatlar"],
        "Maddi Duran Varlıklar": ["Bina", "Arsa", "Araç", "Makine", "Demirbaş"],
        "Maddi Olmayan Duran Varlıklar": ["Marka", "Patent", "Yazılım", "Know-how"],
        "Diğer Duran Varlıklar": ["Verilen uzun vadeli depozito", "Uzun vadeli alacaklar"],
        "Ticari Borçlar": ["Tedarikçi borçları", "Satıcılar", "Alınan çekler"],
        "Çekler": ["Ödenecek çekler", "Portföydeki çekler"],
        "SGK": ["SGK prim borçları"],
        "KDV": ["Hesaplanan KDV", "İndirilecek KDV"],
        "Muhtasar": ["Muhtasar stopaj borcu"],
        "Diğer Kısa Vadeli Borçlar": ["Personele borçlar", "Ödenecek diğer vergiler", "Kısa vadeli kredi taksitleri"],
        "Uzun Vadeli Borçlar": ["Banka kredileri", "Uzun vadeli ticari borçlar", "Finansal borçlar"],
        "Ödenmiş Sermaye": ["Ortaklarca ödenmiş sermaye"],
        "Geçmiş Yıllar Kar/Zarar": ["Geçmiş yıl karı", "Geçmiş yıl zararı"],
        "Dönem Net Kar/Zarar": ["Dönem net karı", "Dönem net zararı"]
    }

    ana_kalemler = list(alt_kalemler.keys())
    ana_kalem_tutar = {}

    st.header("Bilanço Alt Kalem Girişi")

    otomatik_donem_dosyasi = f"bilanco_{kullanici}_{yil}-{ay}.json"
    otomatik_donem_data = {}
    if os.path.exists(otomatik_donem_dosyasi):
        with open(otomatik_donem_dosyasi, "r") as f:
            otomatik_donem_data = json.load(f)

    # 1. Alt kalem girişlerini ve ana kalem toplamlarını topla
    for kalem in ana_kalemler:
        alt_toplam = 0
        for alt in alt_kalemler[kalem]:
            key = f"{kalem}_{alt}"
            tutar_input = st.session_state.get(key, None)
            if tutar_input is not None and tutar_input > 0:
                alt_toplam += tutar_input
            else:
                tutar_otomatik = otomatik_donem_data.get(key, 0.0)
                alt_toplam += tutar_otomatik
        ana_kalem_tutar[kalem] = alt_toplam

    # 2. Ana başlıkları ve expanderları göster
    for kalem in ana_kalemler:
        st.markdown(f"## {kalem.upper()} {tl_format(ana_kalem_tutar.get(kalem, 0))} ₺")
        with st.expander(f"{kalem} Alt Kalemleri"):
            for alt in alt_kalemler[kalem]:
                key = f"{kalem}_{alt}"
                st.number_input(
                    f"{kalem} - {alt} (₺)", 
                    min_value=0.0, 
                    step=100.0, 
                    format="%.2f", 
                    key=key,
                    value=otomatik_donem_data.get(key, 0.0),
                    disabled=kilitli
                )
                # --- ALT KALEM EK DOSYA & AÇIKLAMA PANELİ ---
                with st.expander(f"({alt}) Ek Dosya, Açıklama & Geçmiş", expanded=False):
                    ack_key_detay = f"{key}_aciklama_detay"
                    aciklama = st.text_area(
                        f"Açıklama / Not (Yalnızca bilgi, toplamı etkilemez)",
                        key=ack_key_detay
                    )

                    dosya_key_detay = f"{key}_dosya_detay"
                    yuklenen = st.file_uploader(
                        f"Fatura / Ek Dosya ({alt})", type=None, key=dosya_key_detay
                    )
                    uploads_dir = "uploads"
                    os.makedirs(uploads_dir, exist_ok=True)
                    yuklenen_dosya_adi = ""
                    if yuklenen is not None:
                        yuklenen_dosya_adi = f"{kalem}_{alt}_{yil}-{ay}_{yuklenen.name}"
                        dosya_path = os.path.join(uploads_dir, yuklenen_dosya_adi)
                        with open(dosya_path, "wb") as f:
                            import shutil
                            shutil.copyfileobj(yuklenen, f)
                        st.success("Dosya yüklendi!")
                        st.markdown(f"[Yüklenen Dosya]({dosya_path})")

                    # Kalıcı audit trail JSON dosyasına kaydet
                    log_file = f"logs/detay_log_{yil}-{ay}_{kalem}_{alt}.json"
                    os.makedirs("logs", exist_ok=True)
                    if st.button(f"{alt} İçin Detay Kayıt", key=f"{key}_audit_detay"):
                        if aciklama or yuklenen_dosya_adi:
                            kayit = {
                                "t": str(datetime.datetime.now()),
                                "kullanici": kullanici,
                                "aciklama": aciklama,
                                "dosya": yuklenen_dosya_adi
                            }
                            with open(log_file, "a", encoding="utf-8") as logf:
                                import json
                                logf.write(json.dumps(kayit, ensure_ascii=False) + "\n")
                            st.success("Detay kaydedildi ve geçmişe eklendi.")
                    # Son 5 kalıcı kaydı göster
                    if os.path.exists(log_file):
                        with open(log_file, "r", encoding="utf-8") as logf:
                            lines = logf.readlines()[-5:]
                            for line in reversed(lines):
                                entry = json.loads(line)
                                st.markdown(
                                    f"- <small>{entry['t']} | <b>{entry['kullanici']}</b> | Açıklama: {entry['aciklama']} | Dosya: {entry['dosya']}</small>",
                                    unsafe_allow_html=True
                                )

    # Bilanço kalemlerinin ana grupları (aktif ve pasif)
    aktifler = [
        "Kasa", "Bankalar", "Ticari Alacaklar", "Stoklar", "Diğer Dönen Varlıklar",
        "Maddi Duran Varlıklar", "Maddi Olmayan Duran Varlıklar", "Diğer Duran Varlıklar"
    ]
    pasifler = [
        "Ticari Borçlar", "Çekler", "SGK", "KDV", "Muhtasar", "Diğer Kısa Vadeli Borçlar",
        "Uzun Vadeli Borçlar", "Ödenmiş Sermaye", "Geçmiş Yıllar Kar/Zarar", "Dönem Net Kar/Zarar"
    ]


    # --- Aktif/Pasif grupları ve tablo fonksiyonu ---
    AKTIF = {
        "A. DÖNEN VARLIKLAR": [
            "Kasa", "Bankalar", "Ticari Alacaklar", "Stoklar", "Diğer Dönen Varlıklar"
        ],
        "B. DURAN VARLIKLAR": [
            "Maddi Duran Varlıklar", "Maddi Olmayan Duran Varlıklar", "Diğer Duran Varlıklar"
        ]
    }
    PASIF = {
        "C. KISA VADELİ YABANCI KAYNAKLAR": [
            "Ticari Borçlar", "Çekler", "SGK", "KDV", "Muhtasar", "Diğer Kısa Vadeli Borçlar"
        ],
        "D. UZUN VADELİ YABANCI KAYNAKLAR": [
            "Uzun Vadeli Borçlar"
        ],
        "E. ÖZKAYNAKLAR": [
            "Ödenmiş Sermaye", "Geçmiş Yıllar Kar/Zarar", "Dönem Net Kar/Zarar"
        ]
    }

    def grup_ve_toplam_yaz(grup_dict, ana_kalem_tutar):
        rows = []
        for grup, kalemler in grup_dict.items():
            rows.append([f"**{grup}**", ""])
            toplam = 0
            for kalem in kalemler:
                tutar = ana_kalem_tutar.get(kalem, 0)
                toplam += tutar
                rows.append([kalem, tl_format(tutar)])
            rows.append([f"**{grup} Toplamı**", f"**{tl_format(toplam)}**"])
            rows.append(["", ""])
        return rows

    aktif_rows = grup_ve_toplam_yaz(AKTIF, ana_kalem_tutar)
    pasif_rows = grup_ve_toplam_yaz(PASIF, ana_kalem_tutar)
    aktif_df = pd.DataFrame(aktif_rows, columns=["AKTİF", "Tutar (₺)"])
    pasif_df = pd.DataFrame(pasif_rows, columns=["PASİF", "Tutar (₺)"])
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("AKTİF")
        gb_aktif = GridOptionsBuilder.from_dataframe(aktif_df)
        gb_aktif.configure_default_column(filterable=True, sortable=True, editable=False, resizable=True)
        grid_options_aktif = gb_aktif.build()
        AgGrid(aktif_df, gridOptions=grid_options_aktif, enable_enterprise_modules=True, theme='streamlit')
    with col2:
        st.subheader("PASİF")
        gb_pasif = GridOptionsBuilder.from_dataframe(pasif_df)
        gb_pasif.configure_default_column(filterable=True, sortable=True, editable=False, resizable=True)
        grid_options_pasif = gb_pasif.build()
        AgGrid(pasif_df, gridOptions=grid_options_pasif, enable_enterprise_modules=True, theme='streamlit')

    # Toplam aktif ve pasif
    toplam_aktif = sum([ana_kalem_tutar.get(x, 0) for x in aktifler])
    toplam_pasif = sum([ana_kalem_tutar.get(x, 0) for x in pasifler])

    st.write(f"**Toplam Aktifler:** {tl_format(toplam_aktif)} ₺")
    st.write(f"**Toplam Pasifler + Özkaynak:** {tl_format(toplam_pasif)} ₺")

    if toplam_aktif == toplam_pasif:
        st.success("Bilanço dengede! (Aktif = Pasif)")
    else:
        st.warning("Bilanço dengesiz! (Aktif ve Pasif tutarları eşit değil)")

    st.subheader("Finansal Rasyolar")
    rasyo_aciklamalari = {
        "Cari Oran": "Cari Oran = Dönen Varlıklar / Kısa Vadeli Yükümlülükler",
        "Likidite Oranı": "Likidite Oranı = (Dönen Varlıklar – Stoklar) / Kısa Vadeli Yükümlülükler",
        "Borç/Özkaynak Oranı": "Borç/Özkaynak Oranı = (Kısa + Uzun Vadeli Borçlar) / Özkaynak"
    }
    rasyolar = finansal_rasyolar(ana_kalem_tutar)
    for isim, deger in rasyolar.items():
        renk, durum = rasyo_uyari_degeri(isim, deger)
        st.markdown(
            f"<span style='font-size:1.1em;'><b>{isim}:</b> "
            f"<span style='color:{renk};font-weight:bold;'>{deger:.2f}</span> "
            f"({durum})</span>", unsafe_allow_html=True
        )
        aciklama = rasyo_aciklamalari.get(isim, "")
        if aciklama:
            st.markdown(
                f"<span style='font-size:0.9em; color:gray;'>{aciklama}</span>",
                unsafe_allow_html=True
            )


    def bilanço_muhasebe_format(ana_kalem_tutar):
        rows = []
        rows.append(["", "AKTİF", ""])
        rows.append(["", "I-DÖNEN VARLIKLAR", ""])
        rows.append(["1", "Kasa", tl_format(ana_kalem_tutar.get("Kasa", 0))])
        rows.append(["2", "Bankalar", tl_format(ana_kalem_tutar.get("Bankalar", 0))])
        rows.append(["3", "Ticari Alacaklar", tl_format(ana_kalem_tutar.get("Ticari Alacaklar", 0))])
        rows.append(["4", "Stoklar", tl_format(ana_kalem_tutar.get("Stoklar", 0))])
        rows.append(["", "DÖNEN VARLIKLAR TOPLAMI", tl_format(sum([ana_kalem_tutar.get(x, 0) for x in ['Kasa','Bankalar','Ticari Alacaklar','Stoklar','Diğer Dönen Varlıklar']]))])
        rows.append(["", "II-DURAN VARLIKLAR", ""])
        rows.append(["5", "Maddi Duran Varlıklar", tl_format(ana_kalem_tutar.get("Maddi Duran Varlıklar", 0))])
        rows.append(["6", "Maddi Olmayan Duran Varlıklar", tl_format(ana_kalem_tutar.get("Maddi Olmayan Duran Varlıklar", 0))])
        rows.append(["7", "Diğer Duran Varlıklar", tl_format(ana_kalem_tutar.get("Diğer Duran Varlıklar", 0))])
        rows.append(["", "DURAN VARLIKLAR TOPLAMI", tl_format(sum([ana_kalem_tutar.get(x, 0) for x in ['Maddi Duran Varlıklar','Maddi Olmayan Duran Varlıklar','Diğer Duran Varlıklar']]))])
        rows.append(["", "AKTİF TOPLAMI", tl_format(sum([ana_kalem_tutar.get(x, 0) for x in [
            'Kasa','Bankalar','Ticari Alacaklar','Stoklar','Diğer Dönen Varlıklar',
            'Maddi Duran Varlıklar','Maddi Olmayan Duran Varlıklar','Diğer Duran Varlıklar']]))])
        rows.append(["", "PASİF", ""])
        rows.append(["", "I-KISA VADELİ YABANCI KAYNAKLAR", ""])
        rows.append(["8", "Ticari Borçlar", tl_format(ana_kalem_tutar.get("Ticari Borçlar", 0))])
        rows.append(["9", "Çekler", tl_format(ana_kalem_tutar.get("Çekler", 0))])
        rows.append(["10", "SGK", tl_format(ana_kalem_tutar.get("SGK", 0))])
        rows.append(["11", "KDV", tl_format(ana_kalem_tutar.get("KDV", 0))])
        rows.append(["12", "Muhtasar", tl_format(ana_kalem_tutar.get("Muhtasar", 0))])
        rows.append(["13", "Diğer Kısa Vadeli Borçlar", tl_format(ana_kalem_tutar.get("Diğer Kısa Vadeli Borçlar", 0))])
        rows.append(["", "KISA VADELİ YABANCI KAYNAKLAR TOPLAMI", tl_format(sum([ana_kalem_tutar.get(x, 0) for x in [
            'Ticari Borçlar','Çekler','SGK','KDV','Muhtasar','Diğer Kısa Vadeli Borçlar']]))])
        rows.append(["", "II-UZUN VADELİ YABANCI KAYNAKLAR", ""])
        rows.append(["14", "Uzun Vadeli Borçlar", tl_format(ana_kalem_tutar.get("Uzun Vadeli Borçlar", 0))])
        rows.append(["", "UZUN VADELİ YABANCI KAYNAKLAR TOPLAMI", tl_format(ana_kalem_tutar.get("Uzun Vadeli Borçlar", 0))])
        rows.append(["", "III-ÖZKAYNAKLAR", ""])
        rows.append(["15", "Ödenmiş Sermaye", tl_format(ana_kalem_tutar.get("Ödenmiş Sermaye", 0))])
        rows.append(["16", "Geçmiş Yıllar Kar/Zarar", tl_format(ana_kalem_tutar.get("Geçmiş Yıllar Kar/Zarar", 0))])
        rows.append(["17", "Dönem Net Kar/Zarar", tl_format(ana_kalem_tutar.get("Dönem Net Kar/Zarar", 0))])
        rows.append(["", "ÖZKAYNAKLAR TOPLAMI", tl_format(sum([ana_kalem_tutar.get(x, 0) for x in [
            'Ödenmiş Sermaye','Geçmiş Yıllar Kar/Zarar','Dönem Net Kar/Zarar']]))])
        rows.append(["", "PASİF TOPLAMI", tl_format(sum([ana_kalem_tutar.get(x, 0) for x in [
            'Ticari Borçlar','Çekler','SGK','KDV','Muhtasar','Diğer Kısa Vadeli Borçlar',
            'Uzun Vadeli Borçlar','Ödenmiş Sermaye','Geçmiş Yıllar Kar/Zarar','Dönem Net Kar/Zarar']]))])
        return pd.DataFrame(rows, columns=["KOD", "HESAP ADI", "TUTAR"])

    bilanco_df = bilanço_muhasebe_format(ana_kalem_tutar)
    st.download_button(
        "Excel Olarak İndir",
        data=bilanco_df.to_csv(index=False, sep=';', decimal=',').encode("utf-8"),
        file_name="bilanco.csv"
    )

    st.markdown("---")

    st.subheader("Otomatik Dönemsel Alt Kalem Girişi")

    # 1. Ana kalem seç
    otomatik_ana = st.selectbox(
        "Ana Kalem Seçiniz",
        list(alt_kalemler.keys()),
        disabled=kilitli
    )

    # 2. Seçili ana kalemin alt kalemleri
    secilen_alt_kalem = st.selectbox(
        "Alt Kalem Seçiniz",
        alt_kalemler[otomatik_ana],
        disabled=kilitli
    )

    vade = st.number_input("Vade (Yıl)", min_value=1, max_value=10, value=3, step=1, disabled=kilitli)
    tutar = st.number_input("Yıllık Tutar (₺)", min_value=0.0, step=100.0, format="%.2f", disabled=kilitli)

    if st.button("Otomatik Dönemlere Uygula (Alt Kaleme Yaz)", disabled=kilitli):
        ay_int = int(ay)
        vade_ay = vade * 12
        aylik_tutar = tutar / vade_ay
        for i in range(vade_ay):
            toplam_ay = (ay_int - 1) + i
            yil_hedef = yil + (toplam_ay // 12)
            ay_hedef = (toplam_ay % 12) + 1
            dosya = f"bilanco_{kullanici}_{yil_hedef}-{ay_hedef:02d}.json"
            if os.path.exists(dosya):
                with open(dosya, "r") as f:
                    data = json.load(f)
            else:
                data = {}
            ana_key = f"{otomatik_ana}_{secilen_alt_kalem}"
            mevcut = data.get(ana_key, 0.0)
            data[ana_key] = mevcut + aylik_tutar
            with open(dosya, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        # Otomatik dönemsel giriş sonrası session_state'ten ilgili anahtar sil
        ana_key_session = f"{otomatik_ana}_{secilen_alt_kalem}"
        if ana_key_session in st.session_state:
            del st.session_state[ana_key_session]
        st.session_state["info"] = f"{secilen_alt_kalem} alt kalemine {vade} yıl ({vade_ay} ay) boyunca aylık {tl_format(aylik_tutar)} ₺ yazıldı!"
        st.rerun()

    if "info" in st.session_state:
        st.success(st.session_state["info"])
        del st.session_state["info"]

    kaydet_bilanco_state()


# --- Dönemsel bilanço zaman serisi fonksiyonu ---
def donemsel_bilanco_zaman_serisi(kullanici):
    dosyalar = sorted(glob.glob(f"bilanco_{kullanici}_*.json"))
    donemler = []
    aktifler_list = []
    pasifler_list = []
    for dosya in dosyalar:
        donem = dosya.replace(f"bilanco_{kullanici}_", "").replace(".json", "")
        with open(dosya, "r") as f:
            data = json.load(f)
        ana_kalem_tutar_local = {}
        for k in aktifler + pasifler:
            toplam = 0
            for alt in alt_kalemler[k]:
                key = f"{k}_{alt}"
                toplam += data.get(key, 0)
            ana_kalem_tutar_local[k] = toplam
        donemler.append(donem)
        aktifler_list.append(sum([ana_kalem_tutar_local.get(x, 0) for x in aktifler]))
        pasifler_list.append(sum([ana_kalem_tutar_local.get(x, 0) for x in pasifler]))
    df_zaman = pd.DataFrame({
        "Dönem": donemler,
        "Aktifler": aktifler_list,
        "Pasifler": pasifler_list
    })
    return df_zaman


# --- Grafikler ---
# Aktif (Varlıklar) Dağılımı Grafik
aktif_data = {k: ana_kalem_tutar.get(k, 0) for k in aktifler if ana_kalem_tutar.get(k, 0) > 0}
aktif_df_graph = pd.DataFrame(list(aktif_data.items()), columns=["Varlık", "Tutar"])
st.markdown("#### Aktif (Varlıklar) Dağılımı")
if not aktif_df_graph.empty:
    fig_pie = px.pie(aktif_df_graph, names="Varlık", values="Tutar", hole=0.4, title="Aktif Pasta Grafik")
    st.plotly_chart(fig_pie, use_container_width=True)
    fig_bar = px.bar(aktif_df_graph, x="Varlık", y="Tutar", title="Aktif Çubuk Grafik")
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("Aktif (Varlıklar) için veri yok.")

# Pasif (Borç ve Özkaynak) Dağılımı Grafik
pasif_data = {k: ana_kalem_tutar.get(k, 0) for k in pasifler if ana_kalem_tutar.get(k, 0) > 0}
pasif_df_graph = pd.DataFrame(list(pasif_data.items()), columns=["Borç/Özkaynak", "Tutar"])
st.markdown("#### Pasif (Borçlar ve Özkaynak) Dağılımı")
if not pasif_df_graph.empty:
    fig_pie_pasif = px.pie(pasif_df_graph, names="Borç/Özkaynak", values="Tutar", hole=0.4, title="Pasif Pasta Grafik")
    st.plotly_chart(fig_pie_pasif, use_container_width=True)
    fig_bar_pasif = px.bar(pasif_df_graph, x="Borç/Özkaynak", y="Tutar", title="Pasif Çubuk Grafik")
    st.plotly_chart(fig_bar_pasif, use_container_width=True)
else:
    st.info("Pasif (Borçlar ve Özkaynak) için veri yok.")

# Aktif/Pasif Zaman Serisi (Dönemsel Değişim)
st.markdown("#### Aktif/Pasif Zaman Serisi (Dönemsel Değişim)")
df_zaman = donemsel_bilanco_zaman_serisi(kullanici)
if not df_zaman.empty:
    fig = px.line(df_zaman, x="Dönem", y=["Aktifler", "Pasifler"], markers=True, title="Dönemsel Aktif/Pasif Değişimi")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Henüz geçmiş dönem verisi yok.")

# --- Diğer Tabloya Geç ---
st.markdown("---")
st.markdown("### 💸 Diğer Tabloya Geç")
if st.button("Nakit Akım Tablosuna Geç"):
    st.info("Nakit akım tablosuna geçmek için ana menüden veya doğrudan nakit_akim_app.py dosyasını çalıştırabilirsiniz. (Not: Streamlit çoklu app geçişini otomatik olarak desteklemez, ancak bir başlatıcı veya ana menü üzerinden geçiş yapılabilir.)")
    st.write("Terminal veya komut satırında şunu çalıştırabilirsin:")
    st.code("streamlit run nakit_akim_app.py")
    st.markdown("""
    [👉 Nakit Akım Tablosuna Gitmek İçin Tıklayın](http://localhost:8501/)
    """)