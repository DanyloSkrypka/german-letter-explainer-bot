"""User-facing texts in Russian (ru) and Ukrainian (uk) + German reply drafts."""
from __future__ import annotations

LANGS = ("ru", "uk")

SENDERS = {
    "ru": {
        "jobcenter": "Jobcenter — центр занятости (Bürgergeld)",
        "finanzamt": "Finanzamt — налоговая",
        "krankenkasse": "Krankenkasse — медицинская страховая касса",
        "vermieter": "Vermieter / Hausverwaltung — арендодатель",
        "auslaenderbehoerde": "Ausländerbehörde — ведомство по делам иностранцев",
        "rundfunk": "Beitragsservice — взнос за радио и ТВ",
        "familienkasse": "Familienkasse — касса детских пособий (Kindergeld)",
        "other": "отправитель не распознан",
    },
    "uk": {
        "jobcenter": "Jobcenter — центр зайнятості (Bürgergeld)",
        "finanzamt": "Finanzamt — податкова",
        "krankenkasse": "Krankenkasse — медична страхова каса",
        "vermieter": "Vermieter / Hausverwaltung — орендодавець",
        "auslaenderbehoerde": "Ausländerbehörde — відомство у справах іноземців",
        "rundfunk": "Beitragsservice — внесок за радіо й ТБ",
        "familienkasse": "Familienkasse — каса дитячих виплат (Kindergeld)",
        "other": "відправника не розпізнано",
    },
}

UI = {
    "ru": {
        "hello": ("👋 Привет! Пришлите <b>фото немецкого письма</b> — от Jobcenter, Finanzamt, Krankenkasse, "
                  "арендодателя или Ausländerbehörde.\n\nЗа ~20 секунд отвечу по-русски: <b>кто пишет, какой срок, "
                  "сколько платить и что делать</b>, и дам черновик ответа на немецком."),
        "choose": "Выберите язык ответа:",
        "lang_set": "✅ Язык: русский. Пришлите фото письма 📸",
        "reading": "🔎 Читаю письмо…",
        "send_photo": "Пришлите фото письма (как фото или как файл-картинку). Сменить язык: /lang",
        "pdf": "PDF пока не поддерживается в демо — пришлите фото или скриншот страницы.",
        "ocr_fail": "😕 Не получилось прочитать текст. Сфотографируйте письмо ровно, при хорошем свете, целиком.",
        "who": "Кто пишет", "what": "Суть", "deadline": "Срок", "amount": "Сумма", "todo": "Что делать",
        "miss": "Если пропустить", "quote": "в письме", "ref": "Номер дела", "list": "Что нужно (из письма)",
        "approx": "≈ посчитано от даты письма", "no_deadline": "срок в письме не найден — проверьте сами",
        "no_amount": "платить ничего не нужно (суммы к оплате не нашёл)",
        "draft": "✉️ <b>Черновик ответа на немецком</b> (замените [ ] своими данными):",
        "disclaimer": ("⚖️ <i>Это не юридическая консультация.</i> Бот переводит и объясняет письмо простыми словами "
                       "(закон RDG). Срок и сумму всегда сверяйте с письмом. Сложный случай — бесплатно помогут: "
                       "Migrationsberatung (MBE/JMD), Verbraucherzentrale, Mieterverein, Beratungshilfe в Amtsgericht."),
        "deleted": "🗑 Фото и текст письма удалены с сервера сразу после ответа.",
        "scam": "🚩 <b>Похоже на мошенничество:</b>",
        "engine_rules": "разбор: локальные правила",
        "engine_llm": "разбор: Claude",
        "btn_ru": "🇷🇺 Русский", "btn_uk": "🇺🇦 Українська",
    },
    "uk": {
        "hello": ("👋 Привіт! Надішліть <b>фото німецького листа</b> — від Jobcenter, Finanzamt, Krankenkasse, "
                  "орендодавця чи Ausländerbehörde.\n\nЗа ~20 секунд відповім українською: <b>хто пише, який строк, "
                  "скільки платити і що робити</b>, і дам чернетку відповіді німецькою."),
        "choose": "Оберіть мову відповіді:",
        "lang_set": "✅ Мова: українська. Надішліть фото листа 📸",
        "reading": "🔎 Читаю лист…",
        "send_photo": "Надішліть фото листа (як фото або як файл-зображення). Змінити мову: /lang",
        "pdf": "PDF у демо поки не підтримується — надішліть фото або скріншот сторінки.",
        "ocr_fail": "😕 Не вдалося прочитати текст. Сфотографуйте лист рівно, при гарному світлі, повністю.",
        "who": "Хто пише", "what": "Суть", "deadline": "Строк", "amount": "Сума", "todo": "Що робити",
        "miss": "Якщо пропустити", "quote": "у листі", "ref": "Номер справи", "list": "Що потрібно (з листа)",
        "approx": "≈ пораховано від дати листа", "no_deadline": "строк у листі не знайдено — перевірте самі",
        "no_amount": "платити нічого не треба (суми до оплати не знайшов)",
        "draft": "✉️ <b>Чернетка відповіді німецькою</b> (замініть [ ] своїми даними):",
        "disclaimer": ("⚖️ <i>Це не юридична консультація.</i> Бот перекладає й пояснює лист простими словами "
                       "(закон RDG). Строк і суму завжди звіряйте з листом. Складний випадок — безкоштовно допоможуть: "
                       "Migrationsberatung (MBE/JMD), Verbraucherzentrale, Mieterverein, Beratungshilfe в Amtsgericht."),
        "deleted": "🗑 Фото і текст листа видалено з сервера одразу після відповіді.",
        "scam": "🚩 <b>Схоже на шахрайство:</b>",
        "engine_rules": "розбір: локальні правила",
        "engine_llm": "розбір: Claude",
        "btn_ru": "🇷🇺 Русский", "btn_uk": "🇺🇦 Українська",
    },
}

# ---------- per letter type: summary / steps / consequence ----------
# placeholders: {amount} {deadline} {ref}
TYPES = {
    "ru": {
        "mitwirkung": {
            "summary": "Просят донести документы. Пока их нет, заявление не рассматривают.",
            "steps": ["Соберите документы из списка ниже.",
                      "Отправьте <b>копии</b> до {deadline}: онлайн, почтой или лично. Оригиналы не отдавайте.",
                      "Сохраните подтверждение отправки (скриншот, квитанция или отметка о приёме)."],
            "miss": "выплаты могут остановить или отказать (§ 66 SGB I).",
        },
        "bescheid": {
            "summary": "Это решение (Bescheid): налог посчитан, нужно доплатить {amount}.",
            "steps": ["Сверьте цифры со своей декларацией.",
                      "Заплатите {amount} до {deadline}. В назначении платежа — номер {ref}.",
                      "Не согласны — можно подать Einspruch в течение 1 месяца. Нет денег сразу — попросите "
                      "рассрочку (черновик ниже)."],
            "miss": "Säumniszuschlag 1 % за каждый месяц, потом принудительное взыскание.",
        },
        "mahnung": {
            "summary": "Напоминание о долге: оплата не пришла. Сейчас нужно заплатить {amount}.",
            "steps": ["Проверьте выписку: если уже платили — отправьте подтверждение платежа.",
                      "Если долг есть — переведите {amount} до {deadline}.",
                      "Не можете заплатить сразу — попросите рассрочку письменно (черновик ниже)."],
            "miss": "новые пени и Mahnverfahren (взыскание через суд).",
        },
        "abrechnung": {
            "summary": "Годовой расчёт коммунальных (Nebenkosten). Нужно доплатить {amount}.",
            "steps": ["Сверьте предоплаты (Vorauszahlungen) с тем, что вы реально платили.",
                      "Есть сомнения — вы вправе посмотреть счета (Belegeinsicht, § 259 BGB), черновик ниже. "
                      "Возражения — в течение 12 месяцев.",
                      "Если всё верно — переведите {amount} до {deadline}."],
            "miss": "арендодатель может взыскать долг через суд и сослаться на него при споре по договору.",
        },
        "termin": {
            "summary": "Вас приглашают на приём (Termin) {deadline}.",
            "steps": ["Запишите дату и время в календарь.",
                      "Подготовьте документы из списка ниже.",
                      "Не можете прийти — заранее письменно попросите другой день (черновик ниже)."],
            "miss": "дело затянется; при продлении ВНЖ есть риск остаться без действующего документа.",
        },
        "other": {
            "summary": "Тип письма не определил точно. Ниже — срок и сумма, которые нашёл.",
            "steps": ["Сверьте срок и сумму по цитатам из письма.",
                      "Если непонятно — покажите письмо в бесплатной консультации (список внизу)."],
            "miss": "зависит от письма — не откладывайте до последнего дня.",
        },
    },
    "uk": {
        "mitwirkung": {
            "summary": "Просять донести документи. Поки їх немає, заяву не розглядають.",
            "steps": ["Зберіть документи зі списку нижче.",
                      "Надішліть <b>копії</b> до {deadline}: онлайн, поштою або особисто. Оригінали не віддавайте.",
                      "Збережіть підтвердження відправки (скріншот, квитанція або відмітка про прийом)."],
            "miss": "виплати можуть зупинити або відмовити (§ 66 SGB I).",
        },
        "bescheid": {
            "summary": "Це рішення (Bescheid): податок пораховано, треба доплатити {amount}.",
            "steps": ["Звірте цифри зі своєю декларацією.",
                      "Сплатіть {amount} до {deadline}. У призначенні платежу — номер {ref}.",
                      "Не згодні — можна подати Einspruch протягом 1 місяця. Немає грошей одразу — попросіть "
                      "розстрочку (чернетка нижче)."],
            "miss": "Säumniszuschlag 1 % за кожен місяць, потім примусове стягнення.",
        },
        "mahnung": {
            "summary": "Нагадування про борг: оплата не надійшла. Зараз треба сплатити {amount}.",
            "steps": ["Перевірте виписку: якщо вже платили — надішліть підтвердження платежу.",
                      "Якщо борг є — перекажіть {amount} до {deadline}.",
                      "Не можете сплатити одразу — попросіть розстрочку письмово (чернетка нижче)."],
            "miss": "нова пеня і Mahnverfahren (стягнення через суд).",
        },
        "abrechnung": {
            "summary": "Річний розрахунок комунальних (Nebenkosten). Треба доплатити {amount}.",
            "steps": ["Звірте передоплати (Vorauszahlungen) з тим, що ви реально платили.",
                      "Є сумніви — ви маєте право переглянути рахунки (Belegeinsicht, § 259 BGB), чернетка нижче. "
                      "Заперечення — протягом 12 місяців.",
                      "Якщо все правильно — перекажіть {amount} до {deadline}."],
            "miss": "орендодавець може стягнути борг через суд і послатися на нього в спорі щодо договору.",
        },
        "termin": {
            "summary": "Вас запрошують на прийом (Termin) {deadline}.",
            "steps": ["Запишіть дату й час у календар.",
                      "Підготуйте документи зі списку нижче.",
                      "Не можете прийти — заздалегідь письмово попросіть інший день (чернетка нижче)."],
            "miss": "справа затягнеться; при продовженні дозволу є ризик лишитися без чинного документа.",
        },
        "other": {
            "summary": "Тип листа точно не визначив. Нижче — строк і сума, які знайшов.",
            "steps": ["Звірте строк і суму за цитатами з листа.",
                      "Якщо незрозуміло — покажіть лист у безкоштовній консультації (список унизу)."],
            "miss": "залежить від листа — не відкладайте до останнього дня.",
        },
    },
}

# sender-specific overrides of the consequence line
MISS_OVERRIDE = {
    "ru": {("krankenkasse", "mahnung"): "пени, взыскание через суд; при долге страховка покрывает только экстренное лечение."},
    "uk": {("krankenkasse", "mahnung"): "пеня, стягнення через суд; при боргу страховка покриває лише невідкладне лікування."},
}

# ---------- German reply drafts ----------
DRAFT_HEAD = "[Vorname Nachname]\n[Straße Nr.], [PLZ Ort]\n\nAn: {org}\n\nBetreff: Ihr Schreiben vom {letter_date}{ref_part}\n\nSehr geehrte Damen und Herren,\n\n"
DRAFT_FOOT = "\n\nMit freundlichen Grüßen\n[Vorname Nachname]"

DRAFTS = {
    "mitwirkung": ("anbei übersende ich Ihnen die angeforderten Unterlagen:\n{items}\n\n"
                   "Sollten weitere Unterlagen fehlen, bitte ich um eine kurze Nachricht."),
    "bescheid": ("den Betrag von {amount} kann ich derzeit nicht vollständig zum Fälligkeitstag zahlen. "
                 "Ich beantrage daher Ratenzahlung (Stundung nach § 222 AO) in Höhe von [Betrag] € monatlich, "
                 "beginnend am [Datum].\n\nBitte bestätigen Sie mir die Ratenzahlung schriftlich."),
    "mahnung": ("den offenen Betrag von {amount} kann ich derzeit nicht auf einmal zahlen. "
                "Ich bitte um Ratenzahlung in Höhe von [Betrag] € monatlich, beginnend am [Datum].\n\n"
                "Bitte bestätigen Sie mir die Ratenzahlung schriftlich."),
    "abrechnung": ("vielen Dank für die Betriebskostenabrechnung. Bevor ich die Nachzahlung von {amount} leiste, "
                   "möchte ich gemäß § 259 BGB Einsicht in die Abrechnungsbelege nehmen. Bitte nennen Sie mir "
                   "einen Termin oder senden Sie mir Kopien der Belege.\n\n"
                   "Bis zur Belegeinsicht behalte ich mir die Zahlung vor."),
    "termin": ("vielen Dank für die Einladung zum Termin am {deadline}. Leider kann ich den Termin aus "
               "[Grund] nicht wahrnehmen. Ich bitte Sie um einen neuen Termin.\n\n"
               "Ich bin telefonisch unter [Telefonnummer] erreichbar."),
    "other": ("ich habe Ihr Schreiben erhalten. Leider ist mir der Inhalt nicht vollständig verständlich. "
              "Bitte teilen Sie mir kurz mit, was ich tun muss und bis wann."),
}


def plural_days(n: int, lang: str) -> str:
    n_abs = abs(n)
    if lang == "uk":
        forms = ("день", "дні", "днів")
    else:
        forms = ("день", "дня", "дней")
    if n_abs % 10 == 1 and n_abs % 100 != 11:
        w = forms[0]
    elif 2 <= n_abs % 10 <= 4 and not 12 <= n_abs % 100 <= 14:
        w = forms[1]
    else:
        w = forms[2]
    return f"{n_abs} {w}"


def days_left_text(days: int, lang: str) -> str:
    if lang == "uk":
        if days < 0:
            return f"строк минув {plural_days(days, lang)} тому"
        if days == 0:
            return "сьогодні!"
        return f"залишилось {plural_days(days, lang)}"
    if days < 0:
        return f"срок прошёл {plural_days(days, lang)} назад"
    if days == 0:
        return "сегодня!"
    return f"осталось {plural_days(days, lang)}"
