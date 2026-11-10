from __future__ import annotations

from .shared import (
    LABELS,
    _table,
    mask_personal_data,
    protected_aggregate,
    section_title,
    st,
    to_excel_bytes,
)


def _render_database(dff):
    section_title("Base analítica protegida")
    st.caption("A tabela e os arquivos agrupam os processos por município, natureza e tipo de demanda. Identificadores pessoais e processuais foram retirados desta visão; células pequenas seguem a mesma regra de supressão dos gráficos.")
    table = protected_aggregate(dff, ["municipio", "uf", "natureza", "tipo_demanda"])
    table = table[["municipio", "uf", "natureza", "tipo_demanda", "processos", "pacientes", "custo_total", "custo_medio", "tempo_medio"]].sort_values("processos", ascending=False)
    _table(table, height=520)
    if table.empty:
        return
    exported = mask_personal_data(table).rename(columns=LABELS)
    a, b = st.columns(2)
    with a:
        st.download_button("Baixar CSV protegido", data=exported.to_csv(index=False).encode("utf-8-sig"), file_name="petsus_base_analitica_protegida.csv", mime="text/csv", key="protected_csv")
    with b:
        st.download_button("Baixar Excel protegido", data=to_excel_bytes(exported), file_name="petsus_base_analitica_protegida.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="protected_excel")


def render_base_data(dff, base, k, participacao, part_custo, paciente_ids_sel):
    return _render_database(dff)
