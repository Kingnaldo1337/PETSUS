from petsus.dashboard.patient_timeline import timeline_html


def test_current_milestone_is_unique_and_other_states_are_distinct():
    html = timeline_html("Na Justiça", ("Protocolo", "Análise", "Decisão"), 2, "Análise")
    assert html.count('aria-current="step"') == 1
    assert 'care-track-step past' in html
    assert 'care-track-step future' in html
    assert 'Você está nesta etapa' in html


def test_health_not_started_does_not_mark_first_step_as_current():
    html = timeline_html("Na saúde", ("Ordem recebida", "Entrega"), 0, "Aguardando ordem favorável", health=True)
    assert 'aria-current' not in html
    assert 'Aguardando ordem favorável' in html
    assert html.count('care-track-step future') == 2


def test_last_milestone_does_not_claim_treatment_has_ended_and_escapes_data():
    html = timeline_html("Saúde", ("Ordem", "Entrega <registrada>"), 2, "Contínuo", contrast=True)
    assert 'Entrega &lt;registrada&gt;' in html
    assert 'care-track contrast' in html
    assert 'care-track-step future' not in html
    assert 'concluído' not in html
