from petsus.dashboard.patient_accessibility import patient_accessibility_css, patient_speech_html


def test_speech_payload_cannot_break_out_of_script_and_has_accessible_controls():
    html = patient_speech_html('</script><script>alert("x")</script>')
    assert html.count('</script>') == 1
    assert '\\u003c/script>' in html
    assert '<html lang="pt-BR">' in html
    assert 'aria-live="polite"' in html
    assert 'label for="speed"' in html
    for label in ('Ouvir resumo', 'Pausar', 'Continuar', 'Parar'):
        assert label in html
    assert "window.speechSynthesis.pause()" in html
    assert "window.speechSynthesis.resume()" in html
    assert "pagehide" in html
    assert "não oferece leitura em voz alta" in html


def test_audio_controls_honor_visual_preferences():
    html = patient_speech_html('Resumo', contrast=True, large=True)
    assert 'background:#000' in html
    assert 'color:#FFF' in html
    assert 'font:20px' in html


def test_reading_and_motion_styles_are_patient_scoped_and_optional():
    regular = patient_accessibility_css(False, False)
    enabled = patient_accessibility_css(True, True)
    assert 'animation:none' not in regular
    assert 'animation:none' in enabled
    assert 'grid-template-columns:1fr' in enabled
    assert '.stApp:has(.patient-accessibility-marker)' in enabled
