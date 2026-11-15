from petsus.dashboard.chatbot import answer_question


def test_patient_navigation_and_accented_questions():
    assert "Meu acompanhamento" in answer_question("Qual a situação do meu processo?")
    assert "Significado das palavras" in answer_question("O que é RENAME?")
    assert "corridos" in answer_question("Como entender os prazos?")


def test_manager_receives_manager_navigation():
    assert "Andamento" in answer_question("Como acompanhar um processo?", is_manager=True)
    assert "Glossário" in answer_question("O que é PCDT?", is_manager=True)
    assert "data de entrada" in answer_question("Como funciona o período?", is_manager=True)


def test_unknown_question_does_not_invent_answer():
    assert "Ainda não tenho uma resposta" in answer_question("Qual remédio devo tomar?")


def test_contact_and_account_questions():
    assert "início da página" in answer_question("Como encontrar os contatos?")
    assert "Esqueceu sua senha?" in answer_question("Esqueci minha senha")
