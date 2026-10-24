"""CardioRAG V4 — Streamlit presentation interface.

Run from the project root:
    python -m streamlit run app.py
"""

import html
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="CardioRAG | Bilimsel Araştırma Asistanı",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1280px;}
    .hero {padding: 1.5rem 1.7rem; border-radius: 18px;
           background: linear-gradient(115deg,#12263a,#174a5a);
           color: white; margin-bottom: 1.3rem;}
    .hero h1 {margin: 0; font-size: 2.15rem; color: white;}
    .hero p {margin: .5rem 0 0; color: #d5e5eb;}
    .source-card {border: 1px solid rgba(128,128,128,.22);
                  border-radius: 12px; padding: .9rem 1rem; margin: .6rem 0;}
    .small-muted {color: #778899; font-size: .86rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.title("🫀 CardioRAG V4")
    st.caption("Kardiyovasküler literatür için kaynak temelli RAG")
    st.divider()
    st.subheader("RAG işlem hattı")
    st.markdown(
        """
        **1.** Türkçe sorgu → İngilizce arama sorgusu  
        **2.** Multilingual MiniLM + BM25  
        **3.** Reciprocal Rank Fusion (RRF)  
        **4.** Cross-Encoder reranking  
        **5.** Kaynak çeşitliliği + relevance kontrolü  
        **6.** Kaynaklı Türkçe yanıt  
        **7.** Citation & Evidence Validation
        """
    )
    st.info("Evidence Validation'ın mevcut sürümü yanıtı topluca değerlendirir; klinik doğruluk garantisi değildir.")
    st.divider()
    st.subheader("Oturum")
    st.metric("Sorulan soru", len(st.session_state.history))
    if st.button("Soru geçmişini temizle", use_container_width=True):
        st.session_state.history = []
        st.rerun()
    st.caption("Arayüz yerel bilgisayarınızda çalışır. İndeksleme ayrı terminalde devam edebilir.")

st.markdown(
    """
    <div class="hero">
      <h1>CardioRAG</h1>
      <p>Bilimsel makalelere dayalı Türkçe kardiyovasküler araştırma asistanı</p>
    </div>
    """,
    unsafe_allow_html=True,
)

search_tab, history_tab, architecture_tab = st.tabs(
    ["🔎 Araştırma Asistanı", "🕘 Soru Geçmişi", "⚙️ Sistem Hakkında"]
)

with search_tab:
    st.subheader("Literatüre soru sorun")
    st.caption("Yanıtlar indekslenmiş PDF makalelerinden getirilen parçalara dayanır.")
    with st.form("question_form"):
        question = st.text_area(
            "Türkçe sorunuzu yazın",
            placeholder="Örn. Hipertansiyonun kardiyovasküler hastalıklarla ilişkisi nedir?",
            height=110,
        )
        left, right = st.columns([1, 3])
        with left:
            top_k = st.select_slider("Kaynak parçası", options=[3, 5, 7], value=5)
        with right:
            st.write("")
            submitted = st.form_submit_button("🔎 Makalelerde araştır", type="primary", use_container_width=True)

    if submitted:
        if not question.strip():
            st.warning("Lütfen bir soru yazın.")
        else:
            with st.spinner("Makaleler aranıyor, kaynaklar değerlendiriliyor ve yanıt hazırlanıyor..."):
                try:
                    from src.answer_v4 import answer_hybrid_v4
                    answer, sources = answer_hybrid_v4(question.strip(), top_k=top_k)
                except Exception as exc:
                    st.error("RAG sorgusu çalıştırılırken hata oluştu.")
                    with st.expander("Teknik hata ayrıntısı"):
                        st.exception(exc)
                else:
                    st.session_state.history.insert(0, {
                        "question": question.strip(),
                        "answer": answer,
                        "sources": sources,
                        "time": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    })

    if st.session_state.history:
        current = st.session_state.history[0]
        answer = current["answer"]
        sources = current["sources"]
        st.divider()
        st.subheader("Yanıt")
        if not sources:
            st.warning("Yeterince ilgili kaynak bulunamadı. Yanıt üretimi sınırlandırıldı.")
        st.markdown(answer)

        distinct_docs = {
            s.get("pmcid") or s.get("filename") or s.get("chunk_id")
            for s in sources
        }
        a, b, c = st.columns(3)
        a.metric("Getirilen chunk", len(sources))
        b.metric("Benzersiz makale", len(distinct_docs))
        c.metric("Kaynak durumu", "Bulundu" if sources else "Yetersiz")

        if sources:
            st.subheader("Bilimsel kaynaklar")
            st.caption("Numaralar yanıt içindeki atıflarla eşleşir. Bir makaleden birden fazla chunk gelebilir.")
            for index, source in enumerate(sources, 1):
                number = source.get("number", index)
                title = source.get("title") or source.get("filename") or "Başlık bulunamadı"
                with st.expander(f"[{number}] {title}", expanded=index == 1):
                    st.markdown(f"**PDF:** `{source.get('filename') or '—'}`")
                    st.markdown(f"**Sayfa:** {source.get('page') if source.get('page') is not None else '—'}")
                    st.markdown(f"**PMID:** {source.get('pmid') or '—'}")
                    st.markdown(f"**PMCID:** {source.get('pmcid') or '—'}")
                    st.markdown(f"**DOI:** {source.get('doi') or '—'}")
                    if source.get("rerank_score") is not None:
                        st.markdown(f"**Rerank skoru:** `{source['rerank_score']:.4f}`")
                    if source.get("rrf_score") is not None:
                        st.markdown(f"**RRF skoru:** `{source['rrf_score']:.5f}`")
                    pubmed_url = source.get("pubmed_url")
                    doi_url = source.get("doi_url")
                    if pubmed_url and str(pubmed_url).startswith("https://"):
                        st.link_button("PubMed'de aç ↗", pubmed_url)
                    if doi_url and str(doi_url).startswith("https://"):
                        st.markdown(f"[DOI bağlantısı]({doi_url})")
        st.caption("Araştırma amaçlıdır; klinik tanı veya tedavi önerisi yerine geçmez.")

with history_tab:
    st.subheader("Bu oturumdaki sorular")
    if not st.session_state.history:
        st.info("Henüz soru sorulmadı.")
    for item in st.session_state.history:
        with st.expander(f"{item['time']} · {item['question']}"):
            st.markdown(item["answer"])
            st.caption(f"{len(item['sources'])} kaynak parçası")

with architecture_tab:
    st.subheader("CardioRAG V4 mimarisi")
    st.markdown(
        """
        | Katman | Kullanılan yaklaşım |
        |---|---|
        | Belgeler | PDF → sayfa → metin parçaları |
        | Semantik arama | `paraphrase-multilingual-MiniLM-L12-v2` + ChromaDB |
        | Anahtar kelime arama | SQLite FTS5 / BM25 |
        | Birleştirme | Reciprocal Rank Fusion (RRF) |
        | Yeniden sıralama | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
        | Kaynak seçimi | Makale çeşitliliği, maksimum 2 chunk/makale |
        | Yanıt | Türkçe LLM yanıtı, numaralı atıflar |
        | Kontrol | Relevance threshold, citation ve evidence validation |
        | Metadata | MySQL üzerinden PMID, PMCID, DOI, başlık |
        """
    )
    st.info("Rerank skoru olasılık değildir. Deneysel relevance eşiği mevcut küçük indeks üzerinde test edilmiştir; koleksiyon büyüdüğünde yeniden değerlendirilmelidir.")
