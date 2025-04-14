from openai import AsyncClient

from app.core.config import settings

client = AsyncClient(
    api_key=settings.GPT_API_KEY,
    base_url=f"{settings.GPT_BASE}/v1")


async def moderate_ads(title, about):
    text = (
        f"Ads title: {title}\n"
        f"Ads about: {about}\n\n"
        "Проведи семантический анализ рекламы и выдай вердикт, пропускать её или нет.\n"
        "Вывод должен быть в формате JSON с единственным ключом 'passed':\n"
        "True, если реклама соответствует требованиям стандартам как у современной крупной бигтех компании (не допускаются маты, сомнительное содержание и тд),"
        " этическим нормам и может быть пропущена,\n"
        "False, если реклама не соответствует требованиям и должна быть отклонена.\n\n"
        "Только JSON объект в ответ!"
    )
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": text}],
        temperature=0.2
    )
    print(response)

    return response.choices[0].message.content


async def generate_ad_text(title):
    text = (
        f"Заголовок рекламы: {title}\n"
        "Ты крутой копирайтер и тебе нужно написать текст для рекламы.\n"
        "Составь текст, который заинтересует людей и заставит их кликнуть на рекламу.\n"
        "Вывод должен быть в формате JSON с единственным ключом 'ad_text' и ничего более.\n"
    )
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": text}],
        max_tokens=500,
        temperature=0.8
    )
    print(response)

    return response.choices[0].message.content
