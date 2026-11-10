"""Camada demonstrativa determinística; não consulta bases clínicas ou judiciais.

Os vínculos, custos, componentes, causas e andamentos aqui construídos são
cenários didáticos. Não constituem classificação clínica ou decisão jurídica.
"""
from __future__ import annotations

import re
import unicodedata
import zlib
from datetime import date

import pandas as pd

from petsus.config import APP_TIMEZONE, current_reference_date, salario_minimo_no_ano


def normalize_text(value: object) -> str:
    return unicodedata.normalize("NFKD", str(value).lower().strip()).encode("ascii", "ignore").decode("ascii")


def stable_int(key: object, modulo: int) -> int:
    return zlib.crc32(str(key).encode("utf-8")) % modulo


def stable_choice(key: object, choices):
    return choices[stable_int(key, len(choices))]


def extract_dcb(item: object) -> str:
    return re.sub(r"\s+\d.*$", "", str(item).strip()).strip()


JUDICIAL_STAGES = (
    "Documentação preparada", "Processo protocolado", "Processo distribuído",
    "Análise técnica", "Aguardando decisão", "Decisão judicial",
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

# Relações de demonstração plausíveis, sem indicação terapêutica individual.
# Primeiro preservamos o item e corrigimos a categoria/condição incompatíveis.
MEDICINE_CONDITIONS = {
    "adalimumabe": ("Doenças autoimunes", "Imunologia", "M06.9"),
    "vedolizumabe": ("Doenças autoimunes", "Gastroenterologia", "K50.9"),
    "apixabana": ("Doenças cardiovasculares", "Cardiologia", "I48.9"),
    "bevacizumabe": ("Neoplasias", "Oncologia", "C18.9"),
    "enoxaparina": ("Doenças cardiovasculares", "Cardiologia", "I82.9"),
    "cannabidiol": ("Doenças neurológicas", "Neurologia", "G40.9"),
    "insulina": ("Diabetes mellitus", "Endocrinologia", "E10.9"),
    "secuquinumabe": ("Doenças autoimunes", "Imunologia", "L40.9"),
    "nivolumabe": ("Neoplasias", "Oncologia", "C34.9"),
    "omalizumabe": ("Doenças respiratórias crônicas", "Pneumologia", "J45.9"),
    "rituximabe": ("Doenças autoimunes", "Imunologia", "M06.9"),
    "trastuzumabe": ("Neoplasias", "Oncologia", "C50.9"),
    "nusinersen": ("Doenças raras", "Neurologia", "G12.0"),
    "denosumabe": ("Doenças osteomusculares", "Reumatologia", "M81.0"),
    "aflibercepte": ("Doenças oftalmológicas", "Oftalmologia", "H35.3"),
    "pembrolizumabe": ("Neoplasias", "Oncologia", "C34.9"),
    "tocilizumabe": ("Doenças autoimunes", "Imunologia", "M06.9"),
}
MEDICINE_SCENARIOS = {
    # Componente e frequência ilustram um cenário, não a lista oficial RENAME.
    "adalimumabe": ("CEAF", "1A", "A cada 14 dias", 26),
    "vedolizumabe": ("CEAF", "1A", "A cada 8 semanas", 6),
    "apixabana": ("Não incorporado", "Não incorporado", "2x ao dia", 730),
    "bevacizumabe": ("AF Onco", "Oncologia", "A cada 14 dias", 26),
    "enoxaparina": ("CEAF", "1A", "1x ao dia", 365),
    "cannabidiol": ("Não incorporado", "Não incorporado", "2x ao dia", 730),
    "insulina": ("CEAF", "1A", "1x ao dia", 365),
    "secuquinumabe": ("CEAF", "1A", "A cada 28 dias", 13),
    "nivolumabe": ("AF Onco", "Oncologia", "A cada 28 dias", 13),
    "omalizumabe": ("CEAF", "1A", "A cada 28 dias", 13),
    "rituximabe": ("CEAF", "1A", "A cada 6 meses", 2),
    "trastuzumabe": ("AF Onco", "Oncologia", "A cada 21 dias", 17),
    "nusinersen": ("CEAF", "1A", "A cada 4 meses", 3),
    "denosumabe": ("Não incorporado", "Não incorporado", "A cada 6 meses", 2),
    "aflibercepte": ("CEAF", "1A", "A cada 8 semanas", 6),
    "pembrolizumabe": ("AF Onco", "Oncologia", "A cada 21 dias", 17),
    "tocilizumabe": ("CEAF", "1A", "A cada 28 dias", 13),
}
SPECIALTIES = {
    "Diabetes mellitus": "Endocrinologia", "Neoplasias": "Oncologia",
    "Doenças cardiovasculares": "Cardiologia", "Transtornos mentais": "Psiquiatria",
    "Doenças respiratórias crônicas": "Pneumologia", "Doenças raras": "Neurologia",
    "Doenças autoimunes": "Imunologia", "Outras": "Clínica médica",
}
CID_BY_CONDITION = {
    "Diabetes mellitus": "E11.9", "Neoplasias": "C80.9",
    "Doenças cardiovasculares": "I50.9", "Transtornos mentais": "F32.9",
    "Doenças respiratórias crônicas": "J44.9", "Doenças raras": "G12.0",
    "Doenças autoimunes": "M06.9", "Outras": "R69",
}


def _coherent_demand(row) -> dict:
    item = normalize_text(row.item_demandado)
    condition = str(row.condicao_clinica)
    specialty = SPECIALTIES.get(condition, "Clínica médica")
    cid = CID_BY_CONDITION.get(condition, "R69")
    for medicine, values in MEDICINE_CONDITIONS.items():
        if medicine in item:
            return dict(natureza="Medicamentos", tipo_demanda="Medicamentos",
                        condicao_clinica=values[0], especialidade=values[1], cid=values[2])
    if "cirurgia" in item or "procedimento vascular" in item:
        nature, demand = "Cirurgia", "Procedimentos"
        if "ortoped" in item:
            condition, specialty, cid = "Doenças osteomusculares", "Ortopedia", "M17.9"
        elif "cardiac" in item or "vascular" in item:
            condition, specialty, cid = "Doenças cardiovasculares", "Cardiologia", "I25.9"
        elif "oncolog" in item:
            condition, specialty, cid = "Neoplasias", "Oncologia", "C80.9"
        elif "oftalm" in item:
            condition, specialty, cid = "Doenças oftalmológicas", "Oftalmologia", "H26.9"
    elif any(t in item for t in ("ressonancia", "tomografia", "biopsia", "exame genetico", "pet-ct")):
        nature, demand = "Exames", "Exames"
        if "biopsia" in item or "pet-ct" in item:
            condition, specialty, cid = "Neoplasias", "Oncologia", "C80.9"
        elif "genetico" in item:
            condition, specialty, cid = "Doenças raras", "Genética médica", "Q99.9"
    elif any(t in item for t in ("internacao", "uti", "leito", "home care")):
        nature, demand = "Internação", "Internações"
        if "pediatric" in item:
            specialty = "Pediatria"
    elif any(t in item for t in ("cadeira", "equipamento", "curativo", "fralda", "oxigenio", "dieta")):
        nature, demand = "Outros", "Insumos e materiais"
        if "oxigenio" in item:
            condition, specialty, cid = "Doenças respiratórias crônicas", "Pneumologia", "J44.9"
    elif any(t in item for t in ("terapia", "consulta")):
        nature, demand = "Outros", "Consultas e terapias"
    else:
        nature, demand = "Outros", "Apoio ao tratamento"
    return dict(natureza=nature, tipo_demanda=demand, condicao_clinica=condition,
                especialidade=specialty, cid=cid)


def _reference(reference_date: date | str | pd.Timestamp | None) -> pd.Timestamp:
    result = pd.Timestamp(reference_date or current_reference_date())
    if result.tzinfo is not None:
        result = result.tz_convert(APP_TIMEZONE).tz_localize(None)
    return result.normalize()


def enrich_process_tracking(base: pd.DataFrame, reference_date=None) -> pd.DataFrame:
    """Duas trilhas na mesma data civil de referência, nunca no fim do filtro."""
    d = base.copy()
    reference = _reference(reference_date)
    rows = []
    for row in d.itertuples():
        key = row.processo_id
        start = pd.Timestamp(row.data_ajuizamento).normalize()
        elapsed = (reference - start).days
        if elapsed < 0:
            raise ValueError("Há ajuizamento posterior à data de referência dos cálculos.")
        raw_duration = getattr(row, "tempo_tramitacao_dias", 0)
        duration = max(7, int(raw_duration)) if pd.notna(raw_duration) else 30
        outcome = (
            "Em andamento"
            if pd.isna(row.desfecho) or normalize_text(row.desfecho) in ("", "nan", "pendente", "em andamento")
            else str(row.desfecho).strip()
        )
        if duration > elapsed:
            outcome = "Em andamento"
        judged = outcome in ("Procedente", "Parcialmente procedente", "Improcedente")
        ended = judged or outcome in ("Acordo", "Extinto sem julgamento")
        judgment = start + pd.Timedelta(days=duration) if ended else pd.NaT
        urgent = str(row.urgente) == "Sim"
        granted = urgent and str(row.liminar) == "Sim" and elapsed >= 2 and outcome != "Improcedente"
        raw_liminar = getattr(row, "tempo_liminar_dias", 5)
        urgent_duration = int(raw_liminar) if pd.notna(raw_liminar) else 5
        decision_offset = min(max(2, urgent_duration), 15, elapsed) if granted else None
        if granted and ended:
            decision_offset = min(decision_offset, duration)
        urgent_date = start + pd.Timedelta(days=decision_offset) if granted else pd.NaT
        favorable = granted or outcome in ("Procedente", "Parcialmente procedente", "Acordo")
        decision_date = urgent_date if granted else judgment if favorable else pd.NaT
        notice = decision_date + pd.Timedelta(days=1) if favorable else pd.NaT
        if pd.notna(notice) and notice > reference:
            notice = pd.NaT
        closed = ended and (reference - judgment).days > 90 and stable_int(f"{key}-encerrado", 4) == 0
        closure_date = judgment + pd.Timedelta(days=90) if closed else pd.NaT
        if ended:
            order = 10 if closed else 9
            phase = "Sentença" if judged else "Encerrado por acordo" if outcome == "Acordo" else "Extinto"
        elif granted:
            order = 7 if pd.notna(notice) else 6
            phase = "Cumprimento de decisão" if order == 7 else "Conhecimento"
        else:
            order = min(5, 2 + stable_int(f"{key}-judicial", 4))
            phase = "Conhecimento"
        demand = normalize_text(f"{row.natureza} {row.tipo_demanda}")
        if "medicamento" in demand:
            flow, stages = "Medicamento", MEDICINE_STAGES
        elif "cirurgia" in demand:
            flow, stages = "Cirurgia", SURGERY_STAGES
        else:
            flow, stages = "Tratamento ou serviço", GENERAL_HEALTH_STAGES
        health_order = 0
        if pd.notna(notice):
            days_since_notice = (reference - notice).days
            health_order = min(1 + stable_int(f"{key}-saude", len(stages)), 1 + days_since_notice, len(stages))
        health_complete = health_order == len(stages)
        denied = outcome in ("Improcedente", "Extinto sem julgamento")
        health_stage = stages[health_order - 1] if health_order else "Sem ordem de cumprimento após julgamento" if denied else "Aguardando ordem favorável" if not favorable else "Aguardando intimação"
        health_next = stages[health_order] if 0 < health_order < len(stages) else "Manter acompanhamento assistencial" if health_complete else "Consultar representante jurídico sobre a decisão e as opções de atendimento" if denied else "Acompanhar decisão e eventual intimação do órgão de saúde"
        judicial_next = "Acompanhar eventual recurso e trânsito em julgado" if ended else "Aguardar análise do pedido urgente" if urgent and not granted else "Acompanhar próxima decisão judicial"
        deadline_days = stable_choice(f"{key}-prazo", [5, 10, 15, 30]) if pd.notna(notice) else pd.NA
        deadline = notice + pd.Timedelta(days=int(deadline_days)) if pd.notna(notice) else pd.NaT
        overdue = pd.notna(deadline) and reference > deadline and not health_complete
        decision_text = "Liminar concedida" if granted else "Pedido urgente encerrado com o julgamento" if urgent and ended else "Aguardando decisão sobre pedido urgente" if urgent else "Não há pedido urgente neste cenário"
        status = "Prazo vencido - cumprimento pendente" if overdue else "Tratamento em cumprimento contínuo" if health_complete and flow == "Medicamento" else "Cumprimento assistencial concluído" if health_complete else "Cumprimento na saúde em andamento" if health_order else "Andamento judicial encerrado" if closed else "Decisão judicial proferida" if ended else "Atenção prioritária" if urgent and not granted else "Andamento judicial em curso"
        health_date = notice + pd.Timedelta(days=health_order - 1) if health_order else pd.NaT
        last = max([start] + [v for v in (judgment, decision_date, notice, health_date, closure_date) if pd.notna(v)])
        message = f"No Judiciário: {JUDICIAL_STAGES[order - 1]}. Na rede de saúde: {health_stage}."
        rows.append({
            "desfecho": outcome, "fase_processual": phase, "liminar": "Sim" if granted else "Não",
            "tempo_tramitacao_dias": duration if ended else elapsed,
            "tempo_decorrido_dias": elapsed,
            "tempo_liminar_dias": decision_offset if granted else float("nan"),
            "data_julgamento": judgment if judged else pd.NaT,
            "data_desfecho": judgment,
            "data_encerramento": closure_date,
            "etapa_andamento": JUDICIAL_STAGES[order - 1], "etapa_ordem": order,
            "status_andamento": status, "etapa_judicial": JUDICIAL_STAGES[order - 1],
            "etapa_judicial_ordem": order, "percentual_judicial": round(order / len(JUDICIAL_STAGES) * 100),
            "etapa_saude": health_stage, "etapa_saude_ordem": health_order,
            "percentual_saude": round(health_order / len(stages) * 100), "tipo_fluxo_saude": flow,
            "decisao_urgencia": decision_text, "data_decisao": decision_date,
            "data_intimacao": notice, "prazo_cumprimento_dias": deadline_days,
            "data_limite_cumprimento": deadline, "indicador_atraso": "Sim" if overdue else "Não",
            "data_movimentacao_saude": health_date,
            "ultima_movimentacao_data": last, "ultima_movimentacao": message,
            "proxima_etapa": health_next if health_order else judicial_next,
            "responsavel_etapa": "Secretaria / ente responsável" if health_order else "Poder Judiciário",
            "mensagem_paciente": message, "origem_informacao": "Simulação PetSUS",
            "proxima_acao_judicial": judicial_next, "proxima_acao_saude": health_next,
            "encerramento_judicial": "Sim" if closed else "Não", "encerramento_assistencial": "Sim" if health_complete and flow != "Medicamento" else "Não",
            "andamento_demonstrativo": "Sim", "data_referencia_calculo": reference,
            "ultima_atualizacao_dados": reference, "geracao_simulacao": reference,
        })
    tracking = pd.DataFrame(rows, index=d.index)
    for column in tracking:
        d[column] = tracking[column]
    d.attrs.update(data_referencia_calculo=reference.date().isoformat(),
                   ultima_atualizacao_dados=reference.date().isoformat(),
                   geracao_simulacao=reference.date().isoformat(),
                   timezone=APP_TIMEZONE, origem="Base sintética; regenerada a cada data de referência")
    return d


def enrich_judicialization(base: pd.DataFrame) -> pd.DataFrame:
    """Causas operacionais simuladas, passíveis de revisão humana."""
    from .prevention import PREVENTION_ACTIONS

    d = base.copy()
    causes = {
        "Medicamentos": ["Falta pontual de medicamento", "Negativa administrativa", "Falha de comunicação", "Demanda de competência de outro ente"],
        "Cirurgia": ["Ausência de vaga", "Demora na regulação", "Falta de prestador", "Falta de encaminhamento adequado"],
        "Exames": ["Demora na regulação", "Falta de oferta", "Serviço disponível, mas não acessado", "Negativa administrativa"],
        "Internação": ["Ausência de vaga", "Demora na regulação", "Falta de prestador", "Demanda de competência de outro ente"],
        "Outros": ["Serviço disponível, mas não acessado", "Falha de comunicação", "Aguardando fluxo regular", "Falta de oferta", "Demora administrativa", "Problema de regulação"],
    }
    avoidable = PREVENTION_ACTIONS
    cause_values = [stable_choice(f"{r.processo_id}-causa", causes.get(r.natureza, causes["Outros"])) for r in d.itertuples()]
    d["causa_judicializacao"] = cause_values
    d["judicializacao_potencialmente_evitavel"] = ["Sim" if c in avoidable else "Não" for c in cause_values]
    d["motivo_potencialmente_evitavel"] = [avoidable.get(c, "Exige avaliação de oferta, cobertura e responsabilidade; sem evidência suficiente no cenário.") for c in cause_values]
    d["disponibilidade_administrativa"] = ["Sim" if c in ("Serviço disponível, mas não acessado", "Falha de comunicação", "Aguardando fluxo regular") else "Não" for c in cause_values]
    return d


def enrich_petsus_fields(base: pd.DataFrame, reference_date=None) -> pd.DataFrame:
    """Gera cenários coerentes sem inferir responsabilidade legal oficial."""
    d = base.copy()
    reference = _reference(reference_date)
    if not d.empty:
        corrected = pd.DataFrame([_coherent_demand(row) for row in d.itertuples()], index=d.index)
        for column in corrected:
            d[column] = corrected[column]
        pediatric = d["item_demandado"].map(normalize_text).str.contains("internacao pediatrica")
        d.loc[pediatric & pd.to_numeric(d["idade"], errors="coerce").ge(18), "item_demandado"] = "Internação clínica"
        adult_icu = d["item_demandado"].map(normalize_text).eq("uti adulto")
        d.loc[adult_icu & pd.to_numeric(d["idade"], errors="coerce").lt(18), "item_demandado"] = "UTI pediátrica"
        d.loc[d["item_demandado"].map(normalize_text).str.contains("pediatric"), "especialidade"] = "Pediatria"
        d.loc[pediatric & pd.to_numeric(d["idade"], errors="coerce").ge(18), "especialidade"] = "Clínica médica"
        d["doenca_rara"] = d["condicao_clinica"].eq("Doenças raras").map({True: "Sim", False: "Não"})
    # Mesmas faixas de dez anos usadas no gráfico e nos filtros.
    ages = pd.to_numeric(d["idade"], errors="coerce")
    d["faixa_etaria"] = pd.cut(ages, bins=list(range(0, 121, 10)),
        labels=[f"{start} a {start + 9}" for start in range(0, 120, 10)],
        right=False).astype("string").fillna("Não informado")
    d.loc[ages.ge(120), "faixa_etaria"] = "120 ou mais (intervalo aberto)"
    text_fields = ["medicamento_dcb", "rename_incorporado", "componente_sus", "grupo_sus",
                   "apresentacao_padronizada", "pcdt_aplicavel", "pcdt_referencia", "dose_prescrita",
                   "frequencia_administracao", "competencia_petsus", "reu_sugerido", "criterio_competencia",
                   "acima_210_salarios_minimos", "ente_dispensacao_simulado"]
    for column in text_fields:
        d[column] = "Não se aplica"
    for column in ["duracao_meses", "pmvg_referencia", "valor_anual_tratamento", "valor_causa_estimado", "salario_minimo_ajuizamento", "limite_210_sm_ajuizamento"]:
        d[column] = float("nan")
    d["medicamento_petsus"] = d["natureza"].eq("Medicamentos").map({True: "Sim", False: "Não"})
    # Município é ente administrativo, não ramo do Poder Judiciário.
    d["esfera"] = [stable_choice(f"{r.processo_id}-esfera", ["Estadual", "Federal"]) for r in d.itertuples()]
    d["ente_responsavel"] = [stable_choice(f"{r.processo_id}-ente", ["Município", "Estado", "União", "Compartilhada"]) for r in d.itertuples()]
    medicine_rows = []
    for row in d[d["medicamento_petsus"].eq("Sim")].itertuples():
        key = row.processo_id
        component, group, frequency, per_year = next(
            (scenario for name, scenario in MEDICINE_SCENARIOS.items() if name in normalize_text(row.item_demandado)),
            ("Não incorporado", "Não incorporado", "Conferir prescrição", 12),
        )
        incorporated = component != "Não incorporado"
        dispensing = "Município" if component == "CBAF" else "Estado" if component == "CEAF" else "Compartilhada" if component in ("AF Onco", "CESAF") else "A avaliar"
        duration = stable_choice(f"{key}-dur", [6, 12, 12, 24])
        cost = float(row.custo_estimado) if pd.notna(row.custo_estimado) else 0.0
        annual = round(max(cost, 0) * (0.8 + stable_int(f"{key}-anual", 51) / 100), 2)
        salary = salario_minimo_no_ano(pd.Timestamp(row.data_ajuizamento).year)
        threshold = 210 * salary if salary is not None else None
        high = annual >= threshold if threshold is not None else None
        # Cenário didático simplificado: não aplica normas a um caso real.
        federal = component in ("AF Onco", "CESAF") or component == "CEAF" and group == "1A" or not incorporated and high is True
        jurisdiction = "Justiça Federal" if federal else "Justiça Estadual"
        entity = "Compartilhada" if stable_int(f"{key}-compartilhada", 5) == 0 else "União" if federal else "Município" if component == "CBAF" else "Estado"
        protocol = incorporated or stable_int(f"{key}-pcdt", 100) < 28
        medicine_rows.append({
            "index": row.Index, "medicamento_dcb": extract_dcb(row.item_demandado),
            "rename_incorporado": "Sim" if incorporated else "Não", "componente_sus": component,
            "grupo_sus": group, "ente_dispensacao_simulado": dispensing,
            "apresentacao_padronizada": str(row.item_demandado), "pcdt_aplicavel": "Sim" if protocol else "Não",
            "pcdt_referencia": f"Cenário de protocolo para {row.condicao_clinica.lower()}" if protocol else "Sem protocolo no cenário",
            "dose_prescrita": "Conferir dose na prescrição", "frequencia_administracao": frequency,
            "duracao_meses": duration, "pmvg_referencia": round(annual / per_year, 2),
            "valor_anual_tratamento": annual, "valor_causa_estimado": round(annual * min(duration, 12) / 12, 2),
            "salario_minimo_ajuizamento": salary, "limite_210_sm_ajuizamento": threshold,
            "acima_210_salarios_minimos": "Sim" if high else "Não" if high is False else "Ano sem parâmetro cadastrado",
            "competencia_petsus": jurisdiction if incorporated or high is not None else "Não classificada",
            "reu_sugerido": entity, "ente_responsavel": entity,
            "criterio_competencia": f"Componente {component}; 210 SM do ano {pd.Timestamp(row.data_ajuizamento).year}. Validar normas e caso concreto.",
        })
    if medicine_rows:
        medicines = pd.DataFrame(medicine_rows).set_index("index")
        for column in medicines:
            d.loc[medicines.index, column] = medicines[column]
        classified = d["competencia_petsus"].isin(["Justiça Estadual", "Justiça Federal"])
        d.loc[classified, "esfera"] = d.loc[classified, "competencia_petsus"].map({
            "Justiça Estadual": "Estadual", "Justiça Federal": "Federal",
        })
    return enrich_process_tracking(enrich_judicialization(d), reference_date=reference)
