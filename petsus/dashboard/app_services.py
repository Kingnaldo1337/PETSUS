from __future__ import annotations

import re
import unicodedata
import zlib
from pathlib import Path

import pandas as pd
import streamlit as st

from petsus.config import DATA_FILE, LIMITE_210_SM_2026, REQUIRED_COLUMNS
from petsus.data.loader import DataLoadError, load_process_data

def _cpf_digits(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, int):
        return str(value).zfill(11)
    if isinstance(value, float) and value.is_integer():
        return str(int(value)).zfill(11)
    return re.sub(r"\D", "", str(value))


def _format_cpf(value: object) -> str:
    digits = _cpf_digits(value)
    if len(digits) != 11:
        return str(value)
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _cpf_checksum_valid(digits: str) -> bool:
    """Usado só para evitar que um CPF fictício gerado coincida com um CPF real válido."""
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    nums = [int(x) for x in digits]
    total = sum(nums[i] * (10 - i) for i in range(9))
    d1 = (total * 10 % 11) % 10
    total = sum(nums[i] * (11 - i) for i in range(10))
    d2 = (total * 10 % 11) % 10
    return nums[9] == d1 and nums[10] == d2


def _attach_full_cpf(base: pd.DataFrame) -> pd.DataFrame:
    """Garante uma coluna `cpf` completa.

    Em produção, se a planilha já trouxer `cpf`, `cpf_completo` ou `cpf_paciente`,
    o valor real da fonte é usado. Na base fictícia atual, os dígitos ocultos não
    existem; por isso é criado um CPF de demonstração estável por paciente,
    preservando o prefixo e o sufixo visíveis e evitando CPFs válidos reais.
    """
    d = base.copy()
    for source in ("cpf", "cpf_completo", "cpf_paciente"):
        if source in d.columns:
            values = d[source].map(_cpf_digits)
            invalid = values.str.len().ne(11)
            if invalid.any():
                st.error(f"A coluna '{source}' possui CPF(s) incompleto(s). Corrija a fonte de dados antes de continuar.")
                st.stop()
            d["cpf"] = values.map(_format_cpf)
            d["cpf_origem"] = "Fonte de dados"
            return d

    if "cpf_mascarado" not in d.columns:
        st.error("A base precisa conter uma coluna de CPF completo (`cpf`) ou, para demonstração, `cpf_mascarado`.")
        st.stop()

    patient_rows = (
        d[["paciente_id", "cpf_mascarado"]]
        .drop_duplicates("paciente_id")
        .sort_values("paciente_id")
    )
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for row in patient_rows.itertuples(index=False):
        patient_id = str(row.paciente_id)
        masked_digits = re.sub(r"\D", "", str(row.cpf_mascarado))
        if len(masked_digits) < 5:
            st.error(f"CPF mascarado inválido para o paciente {patient_id}.")
            st.stop()
        prefix, suffix = masked_digits[:3], masked_digits[-2:]
        pid_digits = re.sub(r"\D", "", patient_id)
        base_middle = int(pid_digits or "0") % 1_000_000

        # Usa o ID do paciente como semente. Se, por coincidência, resultar em um
        # CPF matematicamente válido, desloca a parte central para mantê-lo fictício.
        for offset in (0, 500_000, 600_000, 700_000, 800_000, 900_000, 400_000, 300_000, 200_000, 100_000):
            middle = (base_middle + offset) % 1_000_000
            candidate = f"{prefix}{middle:06d}{suffix}"
            if candidate not in used and not _cpf_checksum_valid(candidate):
                used.add(candidate)
                mapping[patient_id] = _format_cpf(candidate)
                break
        else:
            st.error(f"Não foi possível gerar um CPF de demonstração para {patient_id}.")
            st.stop()

    d["cpf"] = d["paciente_id"].astype(str).map(mapping)
    d["cpf_origem"] = "Demonstração"
    return d


@st.cache_data(show_spinner=False)
def load_data(path: Path, modified_at: int, schema_version: str) -> pd.DataFrame:
    # schema_version participa da chave do cache. Ele deve mudar quando novas
    # colunas calculadas forem adicionadas, mesmo que o Excel não seja alterado.
    del schema_version
    try:
        base, invalid_dates = load_process_data(
            path, REQUIRED_COLUMNS, _attach_full_cpf, enrich_petsus_fields
        )
    except DataLoadError as exc:
        st.error(str(exc))
        st.stop()
    if invalid_dates:
        st.warning(f"{invalid_dates} registro(s) com data inválida foram ignorados.")
    base["_search"] = (
        base[["paciente", "paciente_id", "cpf", "processo_id", "medicamento_dcb", "cid"]]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .map(normalize_text)
    )
    return base

def normalize_text(value: object) -> str:
    txt = str(value).lower().strip()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    return txt


def stable_int(key: object, modulo: int) -> int:
    return zlib.crc32(str(key).encode("utf-8")) % modulo


def stable_choice(key: object, choices: list):
    return choices[stable_int(key, len(choices))]


def extract_dcb(item: object) -> str:
    txt = str(item).strip()
    txt = re.sub(r"\s+\d.*$", "", txt).strip()
    return txt or str(item).strip()


JUDICIAL_STAGES = (
    "Documentação preparada", "Processo protocolado", "Processo distribuído",
    "Análise técnica", "Aguardando decisão", "Decisão sobre urgência",
    "Órgão responsável intimado", "Cumprimento em acompanhamento", "Sentença",
    "Recursos / trânsito em julgado / encerramento",
)

MEDICINE_STAGES = (
    "Ordem recebida", "Análise do cumprimento", "Estoque verificado",
    "Aquisição, se necessária", "Produto recebido", "Disponível para dispensação",
    "Paciente comunicado", "Medicamento entregue",
)

SURGERY_STAGES = (
    "Ordem recebida", "Regulação", "Hospital definido", "Pré-operatório",
    "Cirurgia autorizada", "Cirurgia agendada", "Paciente convocado",
    "Cirurgia realizada", "Acompanhamento pós-operatório",
)

GENERAL_HEALTH_STAGES = (
    "Ordem recebida", "Análise do cumprimento", "Regulação ou disponibilidade verificada",
    "Providência administrativa", "Serviço ou item disponibilizado",
    "Paciente comunicado", "Tratamento ou procedimento realizado",
)


def _judicial_stage(row) -> int:
    fase = normalize_text(row.fase_processual)
    desfecho = normalize_text(row.desfecho)
    if any(term in fase or term in desfecho for term in ("arquiv", "encerr", "transit")):
        return 10
    if "recurso" in fase or "segunda instancia" in fase:
        return 10
    if desfecho not in ("", "nan", "em andamento", "pendente", "nao se aplica"):
        return 9
    if "cumprimento" in fase or "execu" in fase:
        return 8
    if str(row.liminar) == "Sim":
        return 6 + stable_int(f"{row.processo_id}-pos-liminar", 3)
    return 2 + stable_int(f"{row.processo_id}-judicial", 4)


def enrich_process_tracking(base: pd.DataFrame) -> pd.DataFrame:
    """Cria duas trilhas demonstrativas: processo judicial e cumprimento na saúde."""
    d = base.copy()
    today = pd.Timestamp.today().normalize()
    tracking_rows = []
    columns = [
        "processo_id", "data_ajuizamento", "fase_processual", "desfecho",
        "tempo_tramitacao_dias", "urgente", "liminar", "natureza", "tipo_demanda",
    ]
    for row in d[columns].itertuples():
        judicial_order = _judicial_stage(row)
        judicial_stage = JUDICIAL_STAGES[judicial_order - 1]
        judicial_next = JUDICIAL_STAGES[judicial_order] if judicial_order < len(JUDICIAL_STAGES) else "Acompanhar trânsito em julgado e arquivamento"

        demand = normalize_text(f"{row.natureza} {row.tipo_demanda}")
        if "medicamento" in demand:
            flow_type, health_stages = "Medicamento", MEDICINE_STAGES
        elif any(term in demand for term in ("cirurgia", "cirurgico", "procedimento")):
            flow_type, health_stages = "Cirurgia", SURGERY_STAGES
        else:
            flow_type, health_stages = "Tratamento ou serviço", GENERAL_HEALTH_STAGES

        outcome = normalize_text(row.desfecho)
        favorable_order = str(row.liminar) == "Sim" or any(term in outcome for term in ("procedente", "parcial"))
        if favorable_order:
            health_order = 1 + stable_int(f"{row.processo_id}-saude", len(health_stages))
            if judicial_order >= 8:
                health_order = max(health_order, min(4, len(health_stages)))
            health_stage = health_stages[health_order - 1]
            health_next = health_stages[health_order] if health_order < len(health_stages) else "Manter acompanhamento assistencial"
        else:
            health_order = 0
            health_stage = "Aguardando ordem favorável"
            health_next = "Iniciar cumprimento após decisão favorável"

        decision = "Liminar concedida" if str(row.liminar) == "Sim" else "Aguardando decisão sobre pedido urgente"
        deadline_days = stable_choice(f"{row.processo_id}-prazo", [5, 10, 15, 30]) if favorable_order else pd.NA
        decision_date = pd.Timestamp(row.data_ajuizamento) + pd.Timedelta(days=stable_choice(f"{row.processo_id}-decisao", [2, 5, 10, 15])) if favorable_order else pd.NaT
        notice_date = decision_date + pd.Timedelta(days=stable_choice(f"{row.processo_id}-intimacao", [1, 2, 3])) if favorable_order else pd.NaT
        deadline_date = notice_date + pd.Timedelta(days=int(deadline_days)) if favorable_order else pd.NaT
        health_complete = health_order == len(health_stages)
        overdue = bool(favorable_order and pd.notna(deadline_date) and today > deadline_date and not health_complete)
        elapsed_days = int(row.tempo_tramitacao_dias) if pd.notna(row.tempo_tramitacao_dias) else 0
        last_date = min(
            pd.Timestamp(row.data_ajuizamento) + pd.Timedelta(days=max(elapsed_days, 0)), today
        )

        if overdue:
            status = "Prazo vencido - cumprimento pendente"
        elif flow_type == "Medicamento" and health_complete:
            status = "Tratamento em cumprimento contínuo"
        elif health_order:
            status = "Cumprimento na saúde em andamento"
        elif str(row.urgente) == "Sim" and judicial_order < 6:
            status = "Atenção prioritária"
        elif judicial_order == 10:
            status = "Andamento judicial encerrado"
        else:
            status = "Andamento judicial em curso"

        patient_message = f"No Judiciário: {judicial_stage}. Na rede de saúde: {health_stage}."
        tracking_rows.append({
            "etapa_andamento": judicial_stage,
            "etapa_ordem": judicial_order,
            "status_andamento": status,
            "etapa_judicial": judicial_stage,
            "etapa_judicial_ordem": judicial_order,
            "percentual_judicial": round(judicial_order / len(JUDICIAL_STAGES) * 100),
            "etapa_saude": health_stage,
            "etapa_saude_ordem": health_order,
            "percentual_saude": round(health_order / len(health_stages) * 100) if health_order else 0,
            "tipo_fluxo_saude": flow_type,
            "decisao_urgencia": decision,
            "data_decisao": decision_date,
            "data_intimacao": notice_date,
            "prazo_cumprimento_dias": deadline_days,
            "data_limite_cumprimento": deadline_date,
            "indicador_atraso": "Sim" if overdue else "Não",
            "ultima_movimentacao_data": last_date,
            "ultima_movimentacao": patient_message,
            "proxima_etapa": health_next if health_order else judicial_next,
            "responsavel_etapa": "Secretaria / ente responsável" if health_order else "Poder Judiciário",
            "mensagem_paciente": patient_message,
            "origem_informacao": "Simulação PetSUS",
            "proxima_acao_judicial": judicial_next,
            "proxima_acao_saude": health_next,
            "encerramento_judicial": "Sim" if judicial_order == len(JUDICIAL_STAGES) else "Não",
            "encerramento_assistencial": "Sim" if health_complete and flow_type != "Medicamento" else "Não",
            "andamento_demonstrativo": "Sim",
        })

    tracking = pd.DataFrame(tracking_rows, index=d.index)
    for column in tracking.columns:
        d[column] = tracking[column]
    return d


def enrich_petsus_fields(base: pd.DataFrame) -> pd.DataFrame:
    """Adiciona os campos de análise de medicamentos do PetSUS.

    A base deste projeto é fictícia. Portanto, os valores abaixo são sintéticos e
    determinísticos, criados apenas para permitir a demonstração dos novos filtros,
    indicadores e dashboards sem representar consulta oficial ao CNJ/CMED/RENAME.
    """
    d = base.copy()
    item_norm = d["item_demandado"].fillna("").map(normalize_text)
    nao_medicamento = item_norm.str.contains(r"dieta|cadeira|oxigenio|curativo|fralda", regex=True)
    med_mask = d["natureza"].eq("Medicamentos") & ~nao_medicamento

    text_fields = [
        "medicamento_petsus", "medicamento_dcb", "cid", "rename_incorporado",
        "componente_sus", "grupo_sus", "apresentacao_padronizada", "pcdt_aplicavel", "pcdt_referencia",
        "dose_prescrita", "frequencia_administracao", "competencia_petsus",
        "reu_sugerido", "criterio_competencia", "acima_210_salarios_minimos",
    ]
    for col in text_fields:
        d[col] = "Não se aplica"
    d["duracao_meses"] = pd.NA
    d["pmvg_referencia"] = pd.NA
    d["valor_anual_tratamento"] = pd.NA
    d["valor_causa_estimado"] = pd.NA
    d.loc[med_mask, "medicamento_petsus"] = "Sim"
    d.loc[~med_mask, "medicamento_petsus"] = "Não"

    cid_map = {
        "Doenças cardiovasculares": ["I10", "I48.9", "I50.9"],
        "Diabetes mellitus": ["E10.9", "E11.9"],
        "Transtornos mentais": ["F32.2", "F41.1", "F31.9"],
        "Neoplasias": ["C50.9", "C34.9", "C18.9", "C61"],
        "Doenças respiratórias crônicas": ["J45.9", "J44.9"],
        "Doenças raras": ["G12.0", "E75.2", "E76.0"],
        "Doenças autoimunes": ["M06.9", "K50.9", "L40.9"],
        "Outras": ["G89.4", "R69"],
    }
    pcdt_map = {
        "Doenças cardiovasculares": "PCDT cardiovascular relacionado à condição",
        "Diabetes mellitus": "PCDT de Diabetes Mellitus",
        "Transtornos mentais": "PCDT relacionado ao transtorno mental",
        "Neoplasias": "Diretriz/PCDT oncológico correspondente",
        "Doenças respiratórias crônicas": "PCDT de Asma/DPOC",
        "Doenças raras": "PCDT da doença rara correspondente",
        "Doenças autoimunes": "PCDT da condição autoimune",
        "Outras": "PCDT relacionado à condição",
    }
    freq_options = [
        ("1x ao dia", 365),
        ("1x por semana", 52),
        ("A cada 14 dias", 26),
        ("A cada 28 dias", 13),
        ("1x ao mês", 12),
    ]
    rows = []
    med_cols = ["processo_id", "item_demandado", "condicao_clinica", "custo_estimado", "uf"]
    for row in d.loc[med_mask, med_cols].itertuples():
        key = row.processo_id
        dcb = extract_dcb(row.item_demandado)
        cid = stable_choice(f"{key}-cid", cid_map.get(row.condicao_clinica, ["R69"]))
        incorporado = "Sim" if stable_int(f"{key}-rename", 100) < 58 else "Não"

        if incorporado == "Sim":
            if row.condicao_clinica == "Neoplasias":
                componente = stable_choice(f"{key}-comp", ["AF Onco", "AF Onco", "CEAF"])
            else:
                componente = stable_choice(f"{key}-comp", ["CEAF", "CEAF", "CEAF", "CBAF", "CBAF", "CESAF"])
            if componente == "CEAF":
                grupo = stable_choice(f"{key}-grupo", ["1A", "1A", "1B", "2", "3"])
            elif componente == "AF Onco":
                grupo = "Oncologia"
            else:
                grupo = componente
        else:
            componente = "Não incorporado"
            grupo = "Não incorporado"

        pcdt = "Sim" if stable_int(f"{key}-pcdt", 100) < (82 if incorporado == "Sim" else 28) else "Não"
        pcdt_ref = pcdt_map.get(row.condicao_clinica, "PCDT relacionado à condição") if pcdt == "Sim" else "Sem PCDT aplicável"
        apresentacao = str(row.item_demandado)
        dose = stable_choice(f"{key}-dose", ["1 unidade por administração", "2 unidades por administração", "Dose conforme prescrição"])
        frequencia, adm_ano = stable_choice(f"{key}-freq", freq_options)
        duracao = stable_choice(f"{key}-dur", [6, 12, 12, 12, 24])

        custo = float(row.custo_estimado or 0)
        fator_anual = 0.80 + stable_int(f"{key}-anual", 51) / 100
        valor_anual = max(custo * fator_anual, 0.0)
        fator_uf = 0.95 + stable_int(f"{row.uf}-pmvg", 11) / 100
        pmvg = (valor_anual / max(adm_ano, 1)) * fator_uf
        valor_causa = valor_anual * min(duracao, 12) / 12
        acima = "Sim" if valor_anual >= LIMITE_210_SM_2026 else "Não"

        if incorporado == "Sim":
            if componente == "AF Onco" or componente == "CESAF" or (componente == "CEAF" and grupo == "1A"):
                competencia = "Justiça Federal"
                reu = "União"
                criterio = f"Medicamento incorporado — {componente} / grupo {grupo}"
            else:
                competencia = "Justiça Estadual"
                reu = "Município" if componente == "CBAF" else "Estado"
                criterio = f"Medicamento incorporado — {componente} / grupo {grupo}"
        else:
            competencia = "Justiça Federal" if acima == "Sim" else "Justiça Estadual"
            reu = "União" if competencia == "Justiça Federal" else stable_choice(f"{key}-reu", ["Estado", "Estado", "Município"])
            criterio = "Não incorporado — custo anual ≥ 210 salários mínimos" if acima == "Sim" else "Não incorporado — custo anual < 210 salários mínimos"

        rows.append({
            "index": row.Index,
            "medicamento_dcb": dcb,
            "cid": cid,
            "rename_incorporado": incorporado,
            "componente_sus": componente,
            "grupo_sus": grupo,
            "apresentacao_padronizada": apresentacao,
            "pcdt_aplicavel": pcdt,
            "pcdt_referencia": pcdt_ref,
            "dose_prescrita": dose,
            "frequencia_administracao": frequencia,
            "duracao_meses": int(duracao),
            "pmvg_referencia": round(pmvg, 2),
            "valor_anual_tratamento": round(valor_anual, 2),
            "valor_causa_estimado": round(valor_causa, 2),
            "competencia_petsus": competencia,
            "reu_sugerido": reu,
            "criterio_competencia": criterio,
            "acima_210_salarios_minimos": acima,
        })

    if rows:
        jud = pd.DataFrame(rows).set_index("index")
        for col in jud.columns:
            d.loc[jud.index, col] = jud[col]

    for col in ["duracao_meses", "pmvg_referencia", "valor_anual_tratamento", "valor_causa_estimado"]:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    return enrich_process_tracking(d)


