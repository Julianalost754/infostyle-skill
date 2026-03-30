#!/usr/bin/env python3
"""
Mechanical eval scorer for /infostyle skill.
Analogous to Karpathy's train.py — outputs a single number.

Usage:
    python eval/score.py eval/outputs/        # Score all output files
    python eval/score.py eval/outputs/case1.md # Score single file

Each output file should contain the skill's response for a test case.
File naming: case{N}.md (matches test case number from test-cases.md)

Output: single number 0-100 (percentage of passed criteria)
"""

import sys
import re
from pathlib import Path

# Стоп-слова для механической проверки (критерий 1)
STOP_WORDS = [
    "очень", "максимально", "уникальный", "уникальная", "уникальное",
    "качественный", "качественная", "качественное", "качественных",
    "инновационный", "инновационная", "инновационное",
    "передовой", "передовая", "передовые", "передовых",
    "высококвалифицированный", "высококвалифицированных",
    "данный", "данная", "данное", "данного",
    "является", "являются", "являясь",
    "осуществлять", "осуществляет", "осуществляем", "осуществление",
    "индивидуальный подход", "команда профессионалов",
    "широкий ассортимент", "динамично развивающ",
    "высокий уровень сервиса", "выгодные условия",
    "комплексные решения", "лидирующий поставщик",
    "клиентоориентированный", "оптимальное соотношение",
]

# Ключевые сущности по кейсам (критерий 6 — смысл сохранён)
# Нужно найти хотя бы половину из списка (substring match)
CASE_ENTITIES = {
    # A: Корпоративные
    1: ["образовательн", "решени", "клиент", "сервис"],
    2: ["IT", "решени", "клиент", "продукт"],
    3: ["разработк", "программ", "проектирован", "внедрен"],
    4: ["интеграц", "платформ", "бизнес"],
    5: ["TechEd", "образовательн", "продукт", "обучени"],
    # B: UI-элементы
    6: ["отправ", "заявк"],
    7: ["поиск", "каталог"],
    8: ["сохранен", "автоматическ"],
    9: ["ошибк", "поддержк", "попроб"],
    10: ["заказ", "оформлен", "заявк"],
    11: ["проект"],
    12: ["загрузк", "подожд"],
    # C: Лендинги
    13: ["презентац", "слайд"],
    14: ["возможност", "бизнес", "ресурс"],
    15: ["тариф", "план", "функци"],
    16: ["пользовател", "платформ"],
    # D: Email
    17: ["функц", "работ", "предложен"],
    18: ["заказ", "доставк", "кабинет"],
    19: ["платформ", "сервис", "возможност"],
    20: ["функци", "вернитесь", "новинк"],
    # E: Формы
    21: ["оформ", "заказ", "цен", "преподавател"],
    22: ["регистрац", "поля", "доступ"],
    23: ["анкет", "мнени", "минут"],
    24: ["форм", "связ", "специалист"],
    # F: Модальные окна
    25: ["удали", "проект"],
    26: ["премиум", "тариф", "инструмент"],
    27: ["cookie", "сайт", "согласи"],
    28: ["скидк", "тариф"],
    # G: Уведомления
    29: ["готов", "работ", "результат"],
    30: ["изменен", "настройк", "профил"],
    31: ["заказ", "доставлен", "пункт"],
    32: ["обслуживан", "сервис", "функци"],
    # H: Юридические
    33: ["ответственност", "сервис", "пользовател"],
    34: ["персональн", "данн", "договор"],
    35: ["соглашени", "условия", "пользовател"],
    # I: E-commerce
    36: ["кресл", "компьютер", "материал"],
    37: ["ноутбук", "работ", "дизайн"],
    38: ["доставк", "территори", "компани"],
    39: ["возврат", "товар", "поддержк"],
    # J: Контент
    40: ["бизнес", "технологи", "трансформац"],
    41: ["продукт", "предложени"],
    42: ["рассылк", "функци", "задач"],
    43: ["специалист", "команд", "компани"],
    # K: Поддержка
    44: ["возврат", "товар", "поддержк"],
    45: ["аутентификац", "безопасност", "аккаунт"],
    46: ["обращени", "поддержк", "информац"],
    47: ["помощник", "вопрос", "проблем"],
    48: ["параметр", "настройк", "профил"],
    # L: Манипуляции
    49: ["мест", "цен"],
    50: ["продукт"],
    51: ["подписк", "функци"],
    # M: Edge cases
    52: ["курс", "модул", "вебинар", "задани"],
    53: ["модул", "курс", "сертификат"],
    54: ["KPI", "данн", "анализ"],
    55: ["мероприяти", "программ"],
    56: ["приложени", "функци", "пользовател"],
}

# Количество слов в оригинальных текстах (из test-cases.md)
# Computed via len(text.strip().split()) on code blocks in test-cases.md
ORIGINAL_WORD_COUNTS = {
    # A: Корпоративные
    1: 26, 2: 34, 3: 29, 4: 21, 5: 32,
    # B: UI-элементы
    6: 8, 7: 5, 8: 6, 9: 20, 10: 22, 11: 5, 12: 11,
    # C: Лендинги
    13: 23, 14: 27, 15: 26, 16: 24,
    # D: Email
    17: 38, 18: 34, 19: 32, 20: 31,
    # E: Формы
    21: 30, 22: 29, 23: 33, 24: 26,
    # F: Модальные окна
    25: 16, 26: 24, 27: 23, 28: 29,
    # G: Уведомления
    29: 17, 30: 20, 31: 22, 32: 22,
    # H: Юридические
    33: 21, 34: 25, 35: 31,
    # I: E-commerce
    36: 29, 37: 23, 38: 25, 39: 34,
    # J: Контент
    40: 30, 41: 24, 42: 29, 43: 36,
    # K: Поддержка
    44: 28, 45: 28, 46: 32, 47: 24, 48: 20,
    # L: Манипуляции
    49: 28, 50: 34, 51: 28,
    # M: Edge cases
    52: 27, 53: 23, 54: 26, 55: 28, 56: 28,
}

# Кейсы, где краткость — цель (auto-pass c2: no gaps)
BREVITY_CASES = {6, 7, 8, 11, 12, 29, 30, 31, 32, 48}

# Юридические кейсы (c7: должен отказаться или предупредить)
LEGAL_CASES = {33, 34, 35}


def check_criterion_1(text: str) -> bool:
    """Стоп-слова убраны? Проверяет только секцию 'Отредактированный текст'."""
    edited = extract_edited_text(text)
    if not edited:
        return True  # Если секции нет — не проваливай (c5 поймает)
    edited_lower = edited.lower()
    for word in STOP_WORDS:
        if word.lower() in edited_lower:
            return False
    return True


def check_criterion_2(text: str, original_word_count: int, case_num: int) -> bool:
    """Пустоты заполнены? Результат не короче 60% оригинала.
    Исключение: UI кнопки, пуш, SMS, тултипы — краткость цель."""
    if case_num in BREVITY_CASES:
        return True  # auto-pass for brevity-focused types

    # Считаем слова в секции "Отредактированный текст"
    edited = extract_edited_text(text)
    if not edited:
        return False

    edited_words = len(edited.split())
    min_words = int(original_word_count * 0.6)
    return edited_words >= min_words


def check_criterion_3(text: str, case_num: int) -> bool:
    """Есть конкретика? Хотя бы одна цифра или единица измерения."""
    edited = extract_edited_text(text)
    if not edited:
        edited = text
    return bool(re.search(r'\d', edited))


def check_criterion_4(text: str) -> bool:
    """Контекст определён? Есть блок с типом текста."""
    return bool(
        re.search(r'[Тт]ип[:\s]', text) or
        re.search(r'[Аа]удитория[:\s]', text) or
        re.search(r'[Кк]онтекст', text)
    )


def check_criterion_5(text: str) -> bool:
    """Формат вывода соблюдён? Все обязательные блоки."""
    has_score_before = bool(re.search(r'[Яя]сность[:\s]*\d', text))
    has_edited = bool(
        re.search(r'[Оо]тредактированный текст', text) or
        re.search(r'[Пп]осле', text)
    )
    has_changes = bool(
        re.search(r'[Чч]то изменилось', text) or
        re.search(r'[Ии]зменени', text) or
        re.search(r'[Пп]очему', text)
    )
    # Check for post-edit score (second occurrence of Ясность or "Оценка (после)")
    has_score_after = bool(
        re.search(r'[Оо]ценка\s*\(после\)', text) or
        len(re.findall(r'[Яя]сность[:\s]*\d', text)) >= 2
    )
    return has_score_before and has_edited and has_changes and has_score_after


def check_criterion_6(text: str, case_num: int) -> bool:
    """Смысл сохранён? Ключевые сущности оригинала в результате."""
    entities = CASE_ENTITIES.get(case_num, [])
    if not entities:
        return True

    text_lower = text.lower()
    found = sum(1 for e in entities if e.lower() in text_lower)
    # Хотя бы половина ключевых сущностей должна присутствовать
    return found >= len(entities) / 2


def check_criterion_7(text: str, case_num: int) -> bool:
    """Юридический текст не тронут? (только для юридических кейсов)"""
    if case_num not in LEGAL_CASES:
        return True  # auto-pass for non-legal cases

    # Должен быть отказ/предупреждение ИЛИ минимальные изменения
    has_warning = bool(
        re.search(r'юрист', text.lower()) or
        re.search(r'юридич', text.lower()) or
        re.search(r'не применя', text.lower()) or
        re.search(r'не рекоменд', text.lower()) or
        re.search(r'правки не применены', text.lower()) or
        re.search(r'точность', text.lower()) or
        re.search(r'правов', text.lower())
    )
    return has_warning


def extract_edited_text(text: str) -> str:
    """Извлечь секцию 'Отредактированный текст' из вывода."""
    # Ищем блок между "Отредактированный текст" и следующим ##
    match = re.search(
        r'##\s*[Оо]тредактированный текст\s*\n(.*?)(?=\n##|\Z)',
        text, re.DOTALL
    )
    if match:
        return match.group(1).strip()

    # Альтернативный формат — блок "После"
    match = re.search(
        r'[Пп]осле[:\s]*\n```?\n?(.*?)```?',
        text, re.DOTALL
    )
    if match:
        return match.group(1).strip()

    return ""


def score_file(filepath: Path) -> dict:
    """Score a single output file. Returns dict of criterion -> pass/fail."""
    text = filepath.read_text(encoding='utf-8')

    # Extract case number from filename
    match = re.search(r'case(\d+)', filepath.name)
    if not match:
        return {}
    case_num = int(match.group(1))

    original_words = ORIGINAL_WORD_COUNTS.get(case_num, 15)

    results = {
        '_case': case_num,
        'c1_stop_words': check_criterion_1(text),
        'c2_no_gaps': check_criterion_2(text, original_words, case_num),
        'c3_specifics': check_criterion_3(text, case_num),
        'c4_context': check_criterion_4(text),
        'c5_format': check_criterion_5(text),
        'c6_meaning': check_criterion_6(text, case_num),
        'c7_legal': check_criterion_7(text, case_num),
    }
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python eval/score.py <output_dir_or_file>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob("case*.md"))
    else:
        print(f"Error: {path} not found")
        sys.exit(1)

    if not files:
        print("Error: no case*.md files found")
        sys.exit(1)

    total_passed = 0
    total_checks = 0

    for f in files:
        results = score_file(f)
        if not results:
            continue

        case_num = results['_case']
        criteria = {k: v for k, v in results.items() if k.startswith('c')}
        passed = sum(1 for k, v in criteria.items() if k != '_case' and v)
        total = sum(1 for k in criteria if k != '_case')

        total_passed += passed
        total_checks += total

        fails = [k for k, v in criteria.items() if k != '_case' and not v]
        status = "PASS" if not fails else f"FAIL({','.join(fails)})"
        print(f"  case{case_num}: {passed}/{total} {status}")

    if total_checks == 0:
        print("0")
        sys.exit(0)

    score = round(total_passed / total_checks * 100, 1)
    print(f"\nScore: {score}")


if __name__ == "__main__":
    main()
