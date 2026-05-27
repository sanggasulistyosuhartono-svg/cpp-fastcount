# =========================
# HEADER LOGO HD
# =========================

st.markdown("""
<style>
    .logo-hd-card {
        background: linear-gradient(90deg, #041b4d 0%, #075bb8 45%, #10c7b7 100%);
        padding: 18px 22px;
        border-radius: 24px;
        box-shadow: 0px 10px 28px rgba(0,0,0,0.14);
        margin-bottom: 24px;
    }

    .logo-hd-card img {
        width: 100%;
        height: auto;
        image-rendering: auto;
        border-radius: 18px;
    }
</style>
""", unsafe_allow_html=True)

if HEADER_LOGO.exists():
    st.markdown('<div class="logo-hd-card">', unsafe_allow_html=True)
    st.image(str(HEADER_LOGO), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("## AquaCount")
