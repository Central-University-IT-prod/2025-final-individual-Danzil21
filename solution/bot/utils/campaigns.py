from bot.utils.api_sdk import CampaignResponse

VALIDATION_MESSAGES = {
    "integer": "⚠️ Пожалуйста, введите целое число (например: 1000)",
    "float": "⚠️ Пожалуйста, введите число с точкой (например: 0.99)",
    "targeting": """⚠️ Пожалуйста, введите таргетинг в формате:
<code>пол,возраст_от,возраст_до,регион</code>

Примеры:
• ALL,18,65,Москва
• male,25,45,Санкт-Петербург
• female,30,50,Казань"""
}

PARAM_EDIT_INSTRUCTIONS = {
    "impressions_limit": {
        "name": "лимит показов",
        "description": "Максимальное количество показов рекламы",
        "format": "целое число",
        "example": "10000"
    },
    "clicks_limit": {
        "name": "лимит кликов",
        "description": "Максимальное количество кликов по рекламе",
        "format": "целое число",
        "example": "1000"
    },
    "cost_per_impression": {
        "name": "цена за показ",
        "description": "Стоимость одного показа рекламы",
        "format": "число с точкой",
        "example": "0.50"
    },
    "cost_per_click": {
        "name": "цена за клик",
        "description": "Стоимость одного клика по рекламе",
        "format": "число с точкой",
        "example": "10.00"
    },
    "ad_title": {
        "name": "заголовок объявления",
        "description": "Заголовок рекламного объявления",
        "format": "текст",
        "example": "Скидка 50% на все товары!"
    },
    "ad_text": {
        "name": "текст объявления",
        "description": "Основной текст рекламного объявления",
        "format": "текст",
        "example": "Только до конца недели! Успейте купить..."
    },
    "start_date": {
        "name": "дата начала",
        "description": "Дата начала показа рекламы",
        "format": "целое число",
        "example": "1"
    },
    "end_date": {
        "name": "дата окончания",
        "description": "Дата окончания показа рекламы",
        "format": "целое число",
        "example": "14"
    },
    "targeting": {
        "name": "настройки таргетинга",
        "description": "Параметры таргетинга через запятую: пол,возраст_от,возраст_до,регион",
        "format": "четыре значения через запятую",
        "example": "ALL,18,65,Москва"
    },
    "ad_photo_url": {
        "name": "фото объявления",
        "description": "Фотография для рекламного объявления (отправьте новое фото или ссылку)",
        "format": "изображение или URL",
        "example": "https://example.com/image.jpg"
    }
}


def format_campaign_message(campaign: CampaignResponse) -> str:
    """Форматирует сообщение с информацией о рекламной кампании"""
    return f"""
<b>📑 Рекламная кампания</b>
ID: <code>{campaign.campaign_id}</code>

<b>📝 Контент:</b>
└ Заголовок: {campaign.ad_title}
└ Текст: {campaign.ad_text}
{'└ Фото: Прикреплено ✅' if campaign.ad_photo_url else '└ Фото: Отсутствует ❌'}

<b>⚙️ Параметры кампании:</b>
└ Лимит показов: {campaign.impressions_limit:,}
└ Лимит кликов: {campaign.clicks_limit:,}
└ Цена за показ: {campaign.cost_per_impression:.2f} ₽
└ Цена за клик: {campaign.cost_per_click:.2f} ₽

<b>📅 Период размещения:</b>
└ Начало: {campaign.start_date}
└ Конец: {campaign.end_date}

<b>🎯 Таргетинг:</b>
{'└ Пол: ' + ('Мужской 👨' if campaign.targeting.gender == 'male' else 'Женский 👩' if campaign.targeting.gender == 'female' else 'Все ⚤')}
└ Возраст: {f'от {campaign.targeting.age_from} до {campaign.targeting.age_to} лет' if campaign.targeting.age_from and campaign.targeting.age_to else 'Без ограничений'}
└ Регион: {campaign.targeting.location if campaign.targeting.location else 'Все регионы'}"""


def get_param_name(param: str) -> str:
    param_names = {
        "impressions_limit": "лимит показов",
        "clicks_limit": "лимит кликов",
        "cost_per_impression": "цена за показ",
        "cost_per_click": "цена за клик",
        "ad_title": "заголовок",
        "ad_text": "текст",
        "start_date": "дату начала",
        "end_date": "дату окончания",
        "targeting": "таргетинг"
    }
    return param_names.get(param, param)
