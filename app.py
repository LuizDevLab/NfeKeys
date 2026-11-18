import re
from collections import Counter

import streamlit as st

# Chave de acesso NF-e (44 posições):
# cUF(2) + AAMM(4) + CNPJ(14) + modelo(2) + série(3) + nNF(9) + tpEmis(1) + cNF(8) + DV(1)
# O CNPJ ocupa as posições 7 a 20 (índices 6:20).
# Aceita CNPJ alfanumérico (12 posições alfanuméricas + 2 dígitos verificadores).
REGEX_CHAVE = re.compile(r"(?<![0-9A-Z])\d{6}[0-9A-Z]{12}\d{26}(?![0-9A-Z])")


def limpar_cnpj(cnpj: str) -> str:
    """Remove pontuação e deixa em maiúsculas (suporta CNPJ alfanumérico)."""
    return re.sub(r"[^0-9A-Z]", "", cnpj.upper())


def extrair_chaves(texto: str) -> list[str]:
    """Extrai todas as chaves de 44 posições do texto, sem duplicatas, mantendo a ordem."""
    chaves = REGEX_CHAVE.findall(texto.upper())
    return list(dict.fromkeys(chaves))


def formatar_cnpj(c: str) -> str:
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"


def filtrar_por_cnpj(chaves: list[str], cnpj: str) -> list[str]:
    return [c for c in chaves if c[6:20] == cnpj]


st.set_page_config(page_title="Filtro de Chaves NF-e por CNPJ", page_icon="🧾")
st.title("🧾 Filtro de Chaves NF-e por CNPJ")
st.caption("Envie o TXT com as chaves do SPED Fiscal e informe o CNPJ para filtrar.")

arquivo = st.file_uploader("Arquivo TXT com as chaves", type=["txt"])
cnpj_input = st.text_input("CNPJ da empresa", placeholder="00.000.000/0000-00")

if arquivo and cnpj_input:
    cnpj = limpar_cnpj(cnpj_input)

    if len(cnpj) != 14:
        st.error("CNPJ inválido: precisa ter 14 posições (sem pontuação).")
        st.stop()

    conteudo = arquivo.read()
    try:
        texto = conteudo.decode("utf-8")
    except UnicodeDecodeError:
        texto = conteudo.decode("latin-1")  # SPED costuma vir em ISO-8859-1

    chaves = extrair_chaves(texto)
    filtradas = filtrar_por_cnpj(chaves, cnpj)

    col1, col2 = st.columns(2)
    col1.metric("Chaves encontradas no arquivo", len(chaves))
    col2.metric(f"Chaves do CNPJ {cnpj_input}", len(filtradas))

    if not chaves:
        st.warning("Nenhuma chave de 44 posições foi encontrada no arquivo.")
    elif not filtradas:
        st.warning(
            "Nenhuma chave foi **emitida** por esse CNPJ. Lembre que a chave só contém o "
            "CNPJ do emitente — notas recebidas de fornecedores têm o CNPJ do fornecedor."
        )
    else:
        saida = "\n".join(filtradas) + "\n"
        st.download_button(
            "⬇️ Baixar TXT filtrado",
            data=saida.encode("utf-8"),
            file_name=f"chaves_{cnpj}.txt",
            mime="text/plain",
        )
        with st.expander("Ver chaves filtradas"):
            st.text(saida)

    if chaves:
        contagem = Counter(c[6:20] for c in chaves)
        with st.expander("CNPJs emitentes encontrados no arquivo", expanded=not filtradas):
            st.dataframe(
                [
                    {"CNPJ emitente": formatar_cnpj(k), "Qtd. de chaves": v}
                    for k, v in contagem.most_common()
                ],
                hide_index=True,
                use_container_width=True,
            )